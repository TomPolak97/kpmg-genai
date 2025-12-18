import logging
import json
import re

from openai import AzureOpenAI
from schema import InjuryForm

# IMPORTANT:
# Logging is configured centrally in logging_config.py
logger = logging.getLogger(__name__)


def safe_json_loads(raw_text: str) -> dict:
    """
    Safely extract and parse a JSON object from raw LLM output.
    """
    try:
        match = re.search(r'\{.*\}', raw_text, flags=re.DOTALL)
        if not match:
            raise ValueError("No JSON object found in LLM response")

        json_str = match.group(0)
        json_str = json_str.replace("'", '"')
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)

        parsed = json.loads(json_str)
        logger.debug("LLM JSON parsed successfully")
        return parsed

    except Exception:
        logger.exception("Failed to parse JSON from LLM output")
        raise


def extract_fields_with_llm(
    ocr_text: str,
    endpoint: str,
    api_key: str,
    deployment: str
) -> dict:
    """
    Extract structured fields from OCR text using Azure OpenAI.
    """
    try:
        schema_json = InjuryForm().model_dump_json(
            indent=2,
            ensure_ascii=False
        )
        logger.info("Schema JSON prepared for LLM extraction")

        client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version="2024-02-15-preview"
        )
        logger.info("AzureOpenAI client initialized")

        system_prompt = f"""
You are an expert at extracting structured data from Israeli National Insurance forms.
Forms may be in Hebrew or English.
Return ONLY valid JSON matching the provided schema.
For missing or unclear fields, return an empty string.
Do not add extra fields.

Here is the JSON schema you must follow exactly:
{schema_json}
"""

        user_prompt = f"""
Extract the following OCR text into the JSON schema above.

OCR TEXT:
{ocr_text}

Return JSON only.
"""

        logger.info("Sending request to LLM")

        response = client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0
        )

        raw_json = response.choices[0].message.content
        logger.info("LLM response received (length=%d)", len(raw_json))

        parsed_json = safe_json_loads(raw_json)

        validated_output = InjuryForm(**parsed_json).model_dump()
        logger.info("LLM output validated against InjuryForm schema")

        return validated_output

    except Exception:
        logger.exception("LLM field extraction failed")
        # Safe fallback: return empty schema
        return InjuryForm().model_dump()
