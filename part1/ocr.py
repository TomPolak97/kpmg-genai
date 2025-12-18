import logging

from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import AzureError

# IMPORTANT:
# Logging is configured centrally in logging_config.py
logger = logging.getLogger(__name__)


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
            raise ValueError("No file bytes provided for OCR extraction")

        logger.info("Initializing Azure Form Recognizer client")

        client = DocumentAnalysisClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(key)
        )

        logger.info("Starting document analysis (prebuilt-layout)")
        poller = client.begin_analyze_document(
            "prebuilt-layout",
            file_bytes
        )

        result = poller.result()
        logger.info(
            "Document analysis completed (pages=%d)",
            len(result.pages)
        )

        text_blocks = []
        for page_index, page in enumerate(result.pages, start=1):
            logger.debug(
                "Processing page %d (lines=%d)",
                page_index,
                len(page.lines)
            )
            for line in page.lines:
                text_blocks.append(line.content)

        extracted_text = "\n".join(text_blocks)
        logger.info(
            "Text extraction completed (characters=%d)",
            len(extracted_text)
        )

        return extracted_text

    except AzureError:
        logger.exception("Azure Form Recognizer API error")
        raise RuntimeError("Azure Form Recognizer API error")

    except Exception:
        logger.exception("OCR extraction failed")
        raise RuntimeError("OCR extraction failed")
