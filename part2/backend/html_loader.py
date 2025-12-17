import os
import time
import logging
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

# Module-level logger
logger = logging.getLogger(__name__)


def generate_embedding_batch(client, texts, service_names, hmos, tiers):
    """
    Generate embeddings for a single batch of texts.

    Inputs are parallel arrays:
    - texts: text to embed
    - service_names, hmos, tiers: metadata aligned by index

    Returns:
    - List of dicts with embedding + metadata
    """
    try:
        logger.debug("Generating embeddings for batch size=%d", len(texts))

        # Call the embedding API for the entire batch at once
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=texts
        )

        # Extract raw embedding vectors from the API response
        embeddings = [res.embedding for res in response.data]

        # Sanity check: embedding count should match input count
        if len(embeddings) != len(texts):
            logger.warning(
                "Embedding count mismatch: expected=%d got=%d",
                len(texts), len(embeddings)
            )

        # Combine embedding + metadata into a structured format
        return [
            {
                "service_name": service_names[i],
                "hmo": hmos[i],
                "tier": tiers[i],
                "text": texts[i],
                "embedding": embeddings[i]
            }
            for i in range(min(len(texts), len(embeddings)))
        ]

    except Exception as e:
        # Any failure in this batch is logged and skipped
        logger.exception(
            "Failed to generate embeddings for batch (size=%d): %s",
            len(texts), e
        )
        return []


def preprocess_html(client, html_dir=None, max_workers=5, batch_size=50):
    """
    Main pipeline:
    1. Load HTML files
    2. Parse medical service tables
    3. Extract service + HMO + tier + benefit text
    4. Convert each benefit to an embedding text
    5. Generate embeddings concurrently in batches

    Returns:
    - List of dicts with keys:
      service_name, hmo, tier, text, embedding
    """
    start_time = time.time()

    # Default HTML directory if not provided
    if html_dir is None:
        html_dir = os.path.join(os.path.dirname(__file__), "phase2_data")

    # Fail fast if directory does not exist
    if not os.path.exists(html_dir):
        logger.error("HTML directory not found: %s", html_dir)
        raise FileNotFoundError(f"HTML directory not found: {html_dir}")

    logger.debug(
        "Starting HTML preprocessing | dir=%s | batch_size=%d | max_workers=%d",
        html_dir, batch_size, max_workers
    )

    # This will collect all embedding tasks before batching
    tasks = []

    # Collect all .html files in the directory
    html_files = [f for f in os.listdir(html_dir) if f.endswith(".html")]
    logger.debug("Found %d HTML files", len(html_files))

    # -------- Parse HTML files --------
    for filename in html_files:
        filepath = os.path.join(html_dir, filename)
        logger.debug("Processing file: %s", filename)

        # Read and parse HTML file
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f, "html.parser")
        except Exception:
            logger.exception("Failed to read HTML file: %s", filepath)
            continue

        # Iterate over every table in the HTML
        for table_idx, table in enumerate(soup.find_all("table")):
            try:
                # Extract table headers (HMO names)
                headers = [th.get_text(strip=True) for th in table.find_all("th")]

                # Skip tables that don't look like service tables
                if len(headers) < 2:
                    logger.warning(
                        "Skipping table %d in %s: insufficient headers",
                        table_idx, filename
                    )
                    continue

                # First header is service name, rest are HMO names
                hmo_names = headers[1:]

                # Iterate over table rows (skip header row)
                for row_idx, row in enumerate(table.find_all("tr")[1:], start=1):
                    cols = row.find_all("td")

                    # Row must contain service name + one column per HMO
                    if len(cols) < len(hmo_names) + 1:
                        logger.warning(
                            "Skipping malformed row %d in table %d (%s)",
                            row_idx, table_idx, filename
                        )
                        continue

                    # First column = medical service name
                    service_name = cols[0].get_text(strip=True)

                    # Iterate over HMO-specific cells
                    for i, hmo in enumerate(hmo_names):
                        cell_html = cols[i + 1].decode_contents()
                        soup_cell = BeautifulSoup(cell_html, "html.parser")

                        # Each <strong> typically represents a tier
                        for strong in soup_cell.find_all("strong"):
                            # Remove trailing ":" from tier name
                            tier = strong.get_text(strip=True).rstrip(":")

                            # The benefit text usually follows the <strong>
                            raw_text = (
                                strong.next_sibling.strip()
                                if strong.next_sibling
                                and isinstance(strong.next_sibling, str)
                                else ""
                            )

                            # Skip empty benefit descriptions
                            if not raw_text:
                                continue

                            # Build the final text that will be embedded
                            embedding_text = (
                                f"שירות רפואי: {service_name}. "
                                f"קופת חולים: {hmo}. "
                                f"מסלול: {tier}. "
                                f"הטבה: {raw_text}"
                            )

                            # Store everything needed for embedding later
                            tasks.append(
                                (embedding_text, service_name, hmo, tier)
                            )

            except Exception:
                # Any unexpected parsing issue is logged per table
                logger.exception(
                    "Failed parsing table %d in file %s",
                    table_idx, filename
                )

    logger.debug("Collected %d embedding tasks", len(tasks))

    # If no valid data was extracted, return early
    if not tasks:
        logger.warning("No tasks collected, returning empty result")
        return []

    # -------- Create batches --------
    # Split all tasks into fixed-size batches for embedding
    batches = [
        tasks[i:i + batch_size]
        for i in range(0, len(tasks), batch_size)
    ]

    logger.debug(
        "Split tasks into %d batches (batch_size=%d)",
        len(batches), batch_size
    )

    all_chunks = []

    # -------- Generate embeddings concurrently --------
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []

        # Submit each batch as a separate async task
        for batch_idx, batch in enumerate(batches):
            logger.debug(
                "Submitting batch %d/%d (size=%d)",
                batch_idx + 1, len(batches), len(batch)
            )

            futures.append(
                executor.submit(
                    generate_embedding_batch,
                    client,
                    [t[0] for t in batch],  # texts
                    [t[1] for t in batch],  # service_names
                    [t[2] for t in batch],  # hmos
                    [t[3] for t in batch]   # tiers
                )
            )

        # Collect results as batches finish
        for future in as_completed(futures):
            try:
                result = future.result()
                all_chunks.extend(result)
            except Exception:
                logger.exception("Embedding batch failed unexpectedly")

    # Log total processing time
    duration = time.time() - start_time
    logger.debug(
        "Finished preprocessing | total_chunks=%d | duration=%.2fs",
        len(all_chunks), duration
    )

    return all_chunks
