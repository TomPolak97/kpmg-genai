from fastapi import APIRouter, Request, HTTPException
from part2.backend.rag_engine import get_relevant_chunks
from part2.backend.prompts import build_q_and_a_prompt
import logging

logger = logging.getLogger(__name__)
q_and_a_router = APIRouter()

@q_and_a_router.post("/ask")
async def ask_question(payload: dict, request: Request):
    try:
        # Validate input
        question = payload.get("question", "").strip()
        user_info = payload.get("user_info", {})
        conversation_history = payload.get("conversation_history", [])
        language = payload.get("language", "english").lower()  # default to English

        if not question:
            logger.warning("Received empty question in payload: %s", payload)
            raise HTTPException(status_code=400, detail="Question is required")
        if "hmo_name" not in user_info or "insurance_tier" not in user_info:
            logger.warning("User info incomplete in payload: %s", payload)
            raise HTTPException(status_code=400, detail="User info incomplete")

        logger.info(
            "Processing question: %s | User HMO: %s | Tier: %s | Language: %s",
            question, user_info["hmo_name"], user_info["insurance_tier"], language
        )

        # Retrieve relevant chunks
        relevant_texts = get_relevant_chunks(
            question, user_info["hmo_name"], user_info["insurance_tier"], request
        )
        logger.debug("Retrieved %d relevant chunks", len(relevant_texts))

        # Build prompt including language
        prompt = build_q_and_a_prompt(
            question, relevant_texts, conversation_history, language=language
        )
        logger.debug("Prompt built successfully | length=%d", len(prompt))

        # Call LLM
        try:
            client = request.app.state.azure_client
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            answer = response.choices[0].message.content.strip()
            logger.info("Generated answer successfully")
        except Exception as e:
            logger.exception("Failed to generate LLM answer")
            raise HTTPException(status_code=500, detail="LLM service error")

        # Update conversation history
        conversation_history.append({"user": question, "bot": answer})

        return {
            "answer": answer,
            "conversation_history": conversation_history,
            "language": language
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unhandled error in /ask endpoint")
        raise HTTPException(status_code=500, detail="Internal server error")
