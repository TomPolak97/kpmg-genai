import os
import time
import logging
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


# =========================
# Embedding helper
# =========================
def generate_embedding_batch(client, texts, service_names, hmos, tiers):
    try:
        logger.debug("Generating embeddings | batch_size=%d", len(texts))

        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=texts
        )

        embeddings = [r.embedding for r in response.data]

        return [
            {
                "service_name": service_names[i],
                "hmo": hmos[i],
                "tier": tiers[i],
                "text": texts[i],
                "embedding": embeddings[i]
            }
            for i in range(len(embeddings))
        ]

    except Exception:
        logger.exception("Embedding batch failed")
        return []


# =========================
# General content extractor
# =========================
def extract_general_chunks(soup):
    """
    Extract non-table content (headings, paragraphs, bullet lists)
    and associate it with the correct medical domain inferred from the nearest <h2>.
    """
    chunks = []
    current_domain = None

    for elem in soup.find_all(["h2", "p", "ul"]):
        if elem.name == "h2":
            current_domain = elem.get_text(strip=True)
            continue

        if not current_domain:
            continue

        if elem.name == "p":
            text = elem.get_text(strip=True)
            if len(text) > 40:
                chunks.append(
                    (f"תחום רפואי: {current_domain}. מידע כללי: {text}",
                     current_domain, "כללי", "כללי")
                )

        if elem.name == "ul" and not elem.find_parent("table"):
            items = [li.get_text(strip=True) for li in elem.find_all("li") if li.get_text(strip=True)]
            if items:
                chunks.append(
                    (f"תחום רפואי: {current_domain}. השירותים כוללים: " + "; ".join(items),
                     current_domain, "כללי", "כללי")
                )

    return chunks


# =========================
# Table extractor
# =========================
def extract_table_chunks(soup):
    """
    Extract structured table information: pricing, benefits, tiers.
    """
    chunks = []
    current_domain_tag = soup.find("h2")
    domain = current_domain_tag.get_text(strip=True) if current_domain_tag else "כללי"

    for table_idx, table in enumerate(soup.find_all("table")):
        try:
            headers = [th.get_text(strip=True) for th in table.find_all("th")]
            if len(headers) < 2:
                continue

            hmo_names = headers[1:]

            for row in table.find_all("tr")[1:]:
                cols = row.find_all("td")
                if len(cols) < len(hmo_names) + 1:
                    continue

                service_name = cols[0].get_text(strip=True)

                for i, hmo in enumerate(hmo_names):
                    cell_soup = BeautifulSoup(cols[i + 1].decode_contents(), "html.parser")

                    for strong in cell_soup.find_all("strong"):
                        tier = strong.get_text(strip=True).rstrip(":")
                        benefit = (
                            strong.next_sibling.strip()
                            if strong.next_sibling and isinstance(strong.next_sibling, str)
                            else ""
                        )
                        if not benefit:
                            continue

                        embedding_text = (
                            f"תחום רפואי: {domain}. "
                            f"שירות: {service_name}. "
                            f"קופת חולים: {hmo}. "
                            f"מסלול ביטוח: {tier}. "
                            f"עלות / מחיר / הנחה: {benefit}"
                        )

                        chunks.append(
                            (embedding_text, service_name, hmo, tier)
                        )

        except Exception:
            logger.exception("Failed parsing table %d", table_idx)

    return chunks


# =========================
# Main pipeline
# =========================
def preprocess_html(client, html_dir=None, max_workers=5, batch_size=50):
    start_time = time.time()

    if html_dir is None:
        html_dir = os.path.join(os.path.dirname(__file__), "phase2_data")

    if not os.path.exists(html_dir):
        raise FileNotFoundError(f"HTML directory not found: {html_dir}")

    tasks = []

    html_files = [f for f in os.listdir(html_dir) if f.endswith(".html")]
    logger.info("Found %d HTML files", len(html_files))

    for filename in html_files:
        filepath = os.path.join(html_dir, filename)
        logger.debug("Processing %s", filename)

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f, "html.parser")
        except Exception:
            logger.exception("Failed reading %s", filename)
            continue

        # Extract general chunks
        tasks.extend(extract_general_chunks(soup))

        # Extract table chunks
        tasks.extend(extract_table_chunks(soup))

    if not tasks:
        logger.warning("No embedding tasks collected")
        return []

    # Batch + concurrency
    batches = [tasks[i:i + batch_size] for i in range(0, len(tasks), batch_size)]
    all_chunks = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(
                generate_embedding_batch,
                client,
                [t[0] for t in batch],
                [t[1] for t in batch],
                [t[2] for t in batch],
                [t[3] for t in batch],
            )
            for batch in batches
        ]

        for future in as_completed(futures):
            all_chunks.extend(future.result())

    logger.info(
        "Finished preprocessing | chunks=%d | time=%.2fs",
        len(all_chunks),
        time.time() - start_time
    )

    return all_chunks
