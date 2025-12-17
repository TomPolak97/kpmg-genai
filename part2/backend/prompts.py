import logging

logger = logging.getLogger(__name__)

def build_user_info_collect_prompt(user_info: dict, language: str = "english") -> str:
    """
    Construct a prompt to ask the LLM to validate user info:
    - Provide user info fields
    - Ask LLM to return JSON with: all_correct, corrected_info, missing_fields
    - Enforce language
    """
    try:
        language = language.lower()

        system_instruction = (
            f"You are a helpful assistant. "
            f"Check the user's personal details and validate each field according to the following rules:\n"
            f"- first_name and last_name: only alphabetic characters (A-Z, a-z, א-ת)\n"
            f"- id_number: exactly 9 digits\n"
            f"- gender: must be 'Male' / 'זכר' or 'Female' / 'נקבה'\n"
            f"- age: integer between 0 and 120\n"
            f"- hmo_name: must be one of ['מכבי', 'מאוחדת', 'כללית']\n"
            f"- hmo_card_number: exactly 9 digits\n"
            f"- insurance_tier: must be one of ['זהב', 'כסף', 'ארד']\n"
            f"Return a strict JSON with three fields:\n"
            f"  'all_correct' (boolean),\n"
            f"  'corrected_info' (dictionary of corrected values),\n"
            f"  'missing_fields' (list of fields that are invalid or missing).\n"
            f"Return the answer in {language}."
        )

        prompt = f"{system_instruction}\n\nUser details:\n{user_info}"
        logger.debug("User info collect prompt built successfully")
        return prompt

    except Exception as e:
        logger.exception("Failed to build user info collect prompt")
        fallback_prompt = f"{system_instruction}\nUser details:\n{user_info}"
        return fallback_prompt


def build_q_and_a_prompt(
    question: str,
    context_texts: list,
    conversation_history: list,
    max_context_chunks: int = 5,
    language: str = "english"
) -> str:
    """
    Construct a structured prompt for Q&A with language enforcement.
    """
    try:
        if not isinstance(question, str) or not question.strip():
            logger.warning("Empty or invalid question provided")
            question = "Unknown question"

        language = language.lower()

        system_instruction = (
            f"You are a helpful medical services assistant. "
            f"Answer the user's questions directly and clearly, as if speaking to the user. "
            f"Base your answers only on the provided context. "
            f"Do not mention the context, sources, or phrases like 'according to the information provided'. "
            f"Answer in {language} **regardless of previous messages**. "
            f"If the context does not contain the answer, respond politely that you don't know."
        )

        # Recent conversation history
        recent_history = conversation_history[-3:] if conversation_history else []
        history_text = ""
        for h in recent_history:
            try:
                history_text += f"User: [{language}] {h['user']}\nBot: {h['bot']}\n"
            except KeyError:
                logger.warning("Malformed conversation history entry: %s", h)
        if history_text:
            history_text = f"Conversation history:\n{history_text}"

        # Top context chunks
        top_contexts = context_texts[:max_context_chunks] if context_texts else []
        context_text = ""
        for chunk in top_contexts:
            if not isinstance(chunk, str):
                logger.warning("Non-string context chunk detected: %s", chunk)
                chunk = str(chunk)
            context_text += f"- {chunk}\n"
        if context_text:
            context_text = f"Relevant context:\n{context_text}"

        question_text = f"[Answer in {language}] {question.strip()}"
        prompt = f"{system_instruction}\n\n{history_text}{context_text}Question:\n{question_text}\nAnswer:"
        logger.debug(
            "Q&A prompt constructed successfully | question=%s | context_chunks=%d | history_entries=%d",
            question, len(top_contexts), len(recent_history)
        )
        return prompt

    except Exception as e:
        logger.exception("Failed to build Q&A prompt")
        fallback_prompt = f"{system_instruction}\nQuestion:\n{question}\nAnswer:"
        return fallback_prompt
