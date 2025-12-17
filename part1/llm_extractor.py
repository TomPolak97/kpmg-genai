from openai import AzureOpenAI
from schema import InjuryForm
import json
import re

def safe_json_loads(raw_text: str):
    match = re.search(r'\{.*\}', raw_text, flags=re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in LLM response")
    json_str = match.group(0)
    json_str = json_str.replace("'", '"')
    json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
    return json.loads(json_str)


def extract_fields_with_llm(ocr_text, endpoint, api_key, deployment):
    # Serialize empty schema to JSON string
    schema_json = InjuryForm().model_dump_json(indent=2, ensure_ascii=False)

    client = AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=api_key,
        api_version="2024-02-15-preview"
    )

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

    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0
    )

    raw_json = response.choices[0].message.content
    print("RAW LLM OUTPUT:\n", raw_json)

    parsed = safe_json_loads(raw_json)
    return InjuryForm(**parsed).model_dump()
