import pydevd_pycharm

pydevd_pycharm.settrace(
    "localhost",  # your PyCharm host
    port=5678,    # debug port
    stdout_to_server=True,
    stderr_to_server=True,
    suspend=False
)

import streamlit as st
from part1.backend.ocr import extract_text_from_document
from part1.backend.llm_extractor import extract_fields_with_llm
from part1.backend.validation import validate_extraction
from part1.backend.part1_config import *
from part1.backend.form_translator import translate_form  # generic translator

st.title("National Insurance Form – Field Extraction")

# Language selection
language = st.radio("Choose output language:", ("English", "Hebrew"))

uploaded = st.file_uploader("Upload PDF or Image", type=["pdf", "jpg", "png"])

if uploaded:
    file_bytes = uploaded.read()

    with st.spinner("Running OCR..."):
        ocr_text = extract_text_from_document(
            file_bytes,
            DOC_INTEL_ENDPOINT,
            DOC_INTEL_KEY
        )

    with st.spinner("Extracting fields..."):
        extracted = extract_fields_with_llm(
            ocr_text,
            AOAI_ENDPOINT,
            AOAI_KEY,
            AOAI_DEPLOYMENT
        )

    validation = validate_extraction(extracted)

    # Translate JSON keys if user chose a language other than English
    if language.lower() != "english":
        extracted = translate_form(extracted, language)
        validation = translate_form(validation, language)

    st.subheader("Extracted JSON")
    st.json(extracted)

    st.subheader("Validation Report")
    st.json(validation)
