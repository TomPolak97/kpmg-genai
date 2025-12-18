import os
import logging
from dotenv import load_dotenv

# IMPORTANT:
# Logging is configured centrally in logging_config.py
logger = logging.getLogger(__name__)


try:
    # ------------------ Load environment variables ------------------
    load_dotenv()
    logger.info("Environment variables loaded from .env file")

    # ------------------ Azure Document Intelligence ------------------
    DOC_INTEL_ENDPOINT = os.getenv("DOC_INTEL_ENDPOINT")
    DOC_INTEL_KEY = os.getenv("DOC_INTEL_KEY")

    if not DOC_INTEL_ENDPOINT or not DOC_INTEL_KEY:
        logger.error("Document Intelligence environment variables are missing")
        raise ValueError(
            "DOC_INTEL_ENDPOINT and DOC_INTEL_KEY must be set in environment variables"
        )

    logger.info("Document Intelligence configuration loaded successfully")

    # ------------------ Azure OpenAI ------------------
    AOAI_ENDPOINT = os.getenv("AOAI_ENDPOINT")
    AOAI_KEY = os.getenv("AOAI_KEY")
    AOAI_DEPLOYMENT = os.getenv("AOAI_DEPLOYMENT", "gpt-4o")

    if not AOAI_ENDPOINT or not AOAI_KEY:
        logger.error("Azure OpenAI environment variables are missing")
        raise ValueError(
            "AOAI_ENDPOINT and AOAI_KEY must be set in environment variables"
        )

    logger.info(
        "Azure OpenAI configuration loaded successfully (deployment=%s)",
        AOAI_DEPLOYMENT
    )

except Exception:
    logger.exception("Failed to load environment configuration")
    raise
