# import pydevd_pycharm
# pydevd_pycharm.settrace(
#     "localhost",  # your PyCharm host
#     port=5678,    # debug port
#     stdout_to_server=True,
#     stderr_to_server=True,
#     suspend=False
# )

import logging
import streamlit as st
from ocr import extract_text_from_document
from llm_extractor import extract_fields_with_llm
from validation import validate_extraction
from part1_config import *
from form_translator import translate_form  # generic translator

# ------------------ Setup logging ------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# ------------------ Streamlit UI ------------------
st.title("National Insurance Form – Field Extraction")

# Language selection
language = st.radio("Choose output language:", ("English", "Hebrew"))

uploaded = st.file_uploader("Upload PDF or Image", type=["pdf", "jpg", "png"])

if uploaded:
    try:
        file_bytes = uploaded.read()
        logger.info("File uploaded successfully: %s", uploaded.name)

        # OCR
        with st.spinner("Running OCR..."):
            try:
                ocr_text = extract_text_from_document(
                    file_bytes,
                    DOC_INTEL_ENDPOINT,
                    DOC_INTEL_KEY
                )
                logger.info("OCR extraction completed. Text length: %d", len(ocr_text))
            except Exception as e:
                logger.exception("OCR extraction failed")
                st.error(f"OCR extraction failed: {e}")
                ocr_text = None

        if ocr_text:
            # Field extraction via LLM
            with st.spinner("Extracting fields..."):
                try:
                    extracted = extract_fields_with_llm(
                        ocr_text,
                        AOAI_ENDPOINT,
                        AOAI_KEY,
                        AOAI_DEPLOYMENT
                    )
                    logger.info("Field extraction completed. Fields extracted: %d", len(extracted))
                except Exception as e:
                    logger.exception("Field extraction failed")
                    st.error(f"Field extraction failed: {e}")
                    extracted = None

            if extracted:
                # Validation
                try:
                    validation = validate_extraction(extracted)
                    logger.info("Validation completed. Issues found: %d", len(validation))
                except Exception as e:
                    logger.exception("Validation failed")
                    st.error(f"Validation failed: {e}")
                    validation = None

                # Translation
                if language.lower() != "english" and extracted:
                    try:
                        extracted = translate_form(extracted, language)
                        if validation:
                            validation = translate_form(validation, language)
                        logger.info("Translation completed for language: %s", language)
                    except Exception as e:
                        logger.exception("Translation failed")
                        st.error(f"Translation failed: {e}")

                # Display results
                if extracted:
                    st.subheader("Extracted JSON")
                    st.json(extracted)
                if validation:
                    st.subheader("Validation Report")
                    st.json(validation)
    except Exception as e:
        logger.exception("Unexpected error during file processing")
        st.error(f"An unexpected error occurred: {e}")
