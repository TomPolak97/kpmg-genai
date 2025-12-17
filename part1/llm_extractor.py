import logging
import json
import re
from openai import AzureOpenAI
from schema import InjuryForm

# ------------------ Setup logging ------------------
logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

def safe_json_loads(raw_text: str):
    try:
        match = re.search(r'\{.*\}', raw_text, flags=re.DOTALL)
        if not match:
            raise ValueError("No JSON object found in LLM response")
        json_str = match.group(0)
        json_str = json_str.replace("'", '"')
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        return json.loads(json_str)
    except Exception as e:
        logger.exception("Failed to parse JSON from LLM output")
        raise ValueError(f"Failed to parse JSON: {e}") from e


def extract_fields_with_llm(ocr_text, endpoint, api_key, deployment):
    try:
        # Serialize empty schema to JSON string
        schema_json = InjuryForm().model_dump_json(indent=2, ensure_ascii=False)
        logger.info("Schema JSON prepared for LLM extraction")

        # Initialize AzureOpenAI client
        client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version="2024-02-15-preview"
        )
        logger.info("AzureOpenAI client initialized")

        # System and user prompts
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

        logger.info("Sending request to LLM...")
        response = client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0
        )

        raw_json = response.choices[0].message.content
        logger.info("LLM response received")
        logger.debug("RAW LLM OUTPUT:\n%s", raw_json)

        parsed = safe_json_loads(raw_json)
        logger.info("LLM output successfully parsed into JSON")

        validated_output = InjuryForm(**parsed).model_dump()
        logger.info("Parsed JSON validated against InjuryForm schema")
        return validated_output

    except Exception as e:
        logger.exception("Failed to extract fields using LLM")
        # Optional: return empty schema or None on failure
        return InjuryForm().model_dump()

