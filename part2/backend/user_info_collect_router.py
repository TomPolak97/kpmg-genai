# user_info_collect_router.py
from fastapi import APIRouter, Request, HTTPException
import logging
import json
import re
from prompts import build_user_info_collect_prompt

logger = logging.getLogger(__name__)
user_info_collect_router = APIRouter()


def extract_final_json(llm_output: str):
    """
    Extract the last JSON code block from LLM output and parse it.
    Cleans comments and trailing commas.
    """
    # Match all ```json ... ``` or ``` ... ``` blocks
    blocks = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", llm_output, re.DOTALL)

    if not blocks:
        # fallback: try parsing the entire output
        try:
            return json.loads(llm_output)
        except json.JSONDecodeError:
            return None

    # Take the last block (assumed final output)
    json_text = blocks[-1]

    # Remove comments like // ...
    json_text = re.sub(r"//.*?$", "", json_text, flags=re.MULTILINE).strip()

    # Remove trailing commas before closing brackets
    json_text = re.sub(r",\s*}", "}", json_text)
    json_text = re.sub(r",\s*]", "]", json_text)

    try:
        return json.loads(json_text)
    except json.JSONDecodeError as e:
        logger.warning("Failed to parse JSON after cleaning: %s", e)
        return None


@user_info_collect_router.post("/verify_user_details")
async def verify_user_details(payload: dict, request: Request):
    """
    Endpoint to verify user details using LLM.

    Expects payload:
    {
        "user_info": { ... },
        "language": "english" | "hebrew"
    }

    Returns:
    {
        "all_correct": bool,
        "corrected_info": dict,
        "missing_fields": list
    }
    """
    try:
        user_info = payload.get("user_info", {})
        language = payload.get("language", "english").lower()

        if not user_info:
            raise HTTPException(status_code=400, detail="User info missing")

        # Build LLM prompt
        validation_prompt = build_user_info_collect_prompt(user_info, language)

        # Call Azure OpenAI client
        client = request.app.state.azure_client
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": validation_prompt}],
            temperature=0
        )

        llm_output = response.choices[0].message.content.strip()
        logger.info("LLM output received")

        # Extract and parse the final JSON
        verification_result = extract_final_json(llm_output)

        # Fallback if parsing failed
        if not verification_result:
            logger.warning("Could not extract valid JSON from LLM response. Returning raw output.")
            verification_result = {
                "all_correct": False,
                "corrected_info": {},
                "missing_fields": [],
                "llm_output": llm_output
            }

        return verification_result

    except Exception as e:
        logger.exception("Failed to verify user details via LLM")
        raise HTTPException(status_code=500, detail="LLM validation error")
