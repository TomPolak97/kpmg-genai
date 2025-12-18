import time
import shutil
import streamlit as st
from logging_config import setup_logging
from ocr import extract_text_from_document
from llm_extractor import extract_fields_with_llm
from validation import validate_extraction
from part1_config import *
from form_translator import translate_form


# ------------------ Helper Functions ------------------
def clear_logs_dir(logs_dir: str = "logs_part1", retries: int = 3, delay: float = 0.5):
    """
    Remove the logs directory if it exists to start fresh logs.
    Retries a few times in case files are locked.
    """
    if os.path.exists(logs_dir):
        # Remove all logging handlers to unlock log files
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
            handler.close()

        for i in range(retries):
            try:
                shutil.rmtree(logs_dir)
                print(f"Removed existing logs directory: {logs_dir}")
                break
            except Exception as e:
                if i < retries - 1:
                    time.sleep(delay)
                else:
                    print(f"Failed to remove {logs_dir}: {e}")


def setup_debug(enable=False, host="localhost", port=5678, suspend=False):
    """Enable PyCharm remote debugging if enable=True."""
    if enable:
        try:
            import pydevd_pycharm
            pydevd_pycharm.settrace(
                host, port=port,
                stdout_to_server=True,
                stderr_to_server=True,
                suspend=suspend
            )
            logger.info("PyCharm debugger attached to %s:%s", host, port)
        except ImportError:
            logger.warning(
                "pydevd_pycharm module not found. Install PyCharm debug egg first."
            )
        except Exception:
            logger.exception("Failed to attach PyCharm debugger")


def run_ocr(file_bytes: bytes) -> str:
    """Run OCR extraction and log results."""
    with st.spinner("Running OCR..."):
        try:
            ocr_text = extract_text_from_document(file_bytes, DOC_INTEL_ENDPOINT, DOC_INTEL_KEY)
            logger.info("OCR completed successfully (text_length=%d)", len(ocr_text))
            return ocr_text
        except Exception:
            logger.exception("OCR extraction failed")
            st.error("OCR extraction failed. Please try another document.")
            return None


def run_llm_extraction(ocr_text: str) -> dict:
    """Run LLM extraction and log results."""
    with st.spinner("Extracting fields..."):
        try:
            extracted = extract_fields_with_llm(ocr_text, AOAI_ENDPOINT, AOAI_KEY, AOAI_DEPLOYMENT)
            logger.info("Field extraction completed (fields=%d)", len(extracted))
            return extracted
        except Exception:
            logger.exception("Field extraction failed")
            st.error("Failed to extract fields using the LLM.")
            return None


def run_validation(extracted: dict) -> dict:
    """Validate extracted fields and log results."""
    try:
        validation = validate_extraction(extracted)
        logger.info("Validation completed (issues=%d)", len(validation))
        return validation
    except Exception:
        logger.exception("Validation failed")
        st.error("Validation failed.")
        return None


def run_translation(extracted: dict, validation: dict, language: str):
    """Translate extracted fields and validation report if needed."""
    if language.lower() == "english":
        return extracted, validation

    try:
        extracted_translated = translate_form(extracted, language)
        validation_translated = translate_form(validation, language) if validation else None
        logger.info("Translation completed (language=%s)", language)
        return extracted_translated, validation_translated
    except Exception:
        logger.exception("Translation failed")
        st.error("Translation failed.")
        return extracted, validation


def display_results(extracted: dict, validation: dict):
    """Display results in Streamlit."""
    st.subheader("Extracted JSON")
    st.json(extracted)

    if validation:
        st.subheader("Validation Report")
        st.json(validation)


# ------------------ Startup ------------------
clear_logs_dir()      # Remove old logs
setup_logging()       # Setup logging
logger = logging.getLogger(__name__)
setup_debug(enable=False)

# ------------------ Streamlit UI ------------------
st.title("National Insurance Form – Field Extraction")
language = st.radio("Choose output language:", ("English", "Hebrew"))
uploaded = st.file_uploader("Upload PDF or Image", type=["pdf", "jpg", "png"])

if uploaded:
    try:
        file_bytes = uploaded.read()
        logger.info("File uploaded: %s (size=%d bytes)", uploaded.name, len(file_bytes))

        ocr_text = run_ocr(file_bytes)
        if not ocr_text:
            ocr_text = None

        if ocr_text:
            extracted = run_llm_extraction(ocr_text)
        else:
            extracted = None

        if extracted:
            validation = run_validation(extracted)
        else:
            validation = None

        if extracted:
            extracted, validation = run_translation(extracted, validation, language)
            display_results(extracted, validation)

    except Exception:
        logger.exception("Unexpected error during file processing")
        st.error("An unexpected error occurred. Please try again.")
