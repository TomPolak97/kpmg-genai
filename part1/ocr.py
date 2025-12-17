import logging
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import AzureError

# ------------------ Setup logging ------------------
logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )


def extract_text_from_document(file_bytes, endpoint, key) -> str:
    """
    Extract text from a PDF or image using Azure Form Recognizer prebuilt-layout model.
    :param file_bytes: bytes of the uploaded document
    :param endpoint: Azure Form Recognizer endpoint
    :param key: Azure Form Recognizer API key
    :return: extracted text as a single string
    """
    try:
        if not file_bytes:
            raise ValueError("No file bytes provided for OCR extraction.")

        logger.info("Initializing Azure Form Recognizer client.")
        client = DocumentAnalysisClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(key)
        )

        logger.info("Starting document analysis with prebuilt-layout model.")
        poller = client.begin_analyze_document(
            "prebuilt-layout",
            file_bytes
        )

        result = poller.result()
        logger.info("Document analysis completed successfully. Pages found: %d", len(result.pages))

        text_blocks = []
        for page_idx, page in enumerate(result.pages, start=1):
            logger.debug("Processing page %d with %d lines", page_idx, len(page.lines))
            for line in page.lines:
                text_blocks.append(line.content)

        extracted_text = "\n".join(text_blocks)
        logger.info("Text extraction completed. Total characters extracted: %d", len(extracted_text))
        return extracted_text

    except AzureError as ae:
        logger.exception("Azure Form Recognizer API error occurred")
        raise RuntimeError(f"Form Recognizer API error: {ae}") from ae
    except Exception as e:
        logger.exception("Unexpected error during OCR extraction")
        raise RuntimeError(f"OCR extraction failed: {e}") from e

