import logging
import numpy as np
from numpy.linalg import norm
from fastapi import Request

logger = logging.getLogger(__name__)

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    try:
        sim = np.dot(a, b) / (norm(a) * norm(b))
        return sim
    except Exception as e:
        logger.exception("Failed to compute cosine similarity")
        return 0.0

def embed_question(question: str, client) -> np.ndarray:
    """Generate embedding for a single question using AzureOpenAI client."""
    try:
        if not question.strip():
            logger.warning("Empty question received for embedding")
            return np.zeros(1536)  # default dimension for text-embedding-ada-002

        resp = client.embeddings.create(model="text-embedding-ada-002", input=question)
        embedding = np.array(resp.data[0].embedding)
        logger.debug("Question embedding generated successfully | shape=%s", embedding.shape)
        return embedding
    except Exception as e:
        logger.exception("Failed to generate embedding for question: %s", question)
        # Return zero vector to avoid crashing downstream
        return np.zeros(1536)

def get_relevant_chunks(question: str, user_hmo: str, user_tier: str, request: Request, top_k=3):
    """
    Filter all_chunks by user HMO/tier and get top_k most relevant chunks using embeddings.
    """
    try:
        client = request.app.state.azure_client
        all_chunks = request.app.state.all_chunks

        if not all_chunks:
            logger.warning("No chunks available in memory")
            return []

        q_emb = embed_question(question, client)

        # Filter by HMO and tier
        filtered = []
        for chunk in all_chunks:
            try:
                if chunk["hmo"] == user_hmo and chunk["tier"] == user_tier:
                    sim = cosine_similarity(q_emb, chunk["embedding"])
                    filtered.append((sim, chunk))
            except KeyError as e:
                logger.warning("Chunk missing expected keys: %s", chunk)

        if not filtered:
            logger.info("No relevant chunks found for HMO=%s, tier=%s", user_hmo, user_tier)
            return []

        # Sort by similarity
        filtered.sort(key=lambda x: x[0], reverse=True)
        top_chunks = [c["text"] for _, c in filtered[:top_k]]

        logger.debug("Top %d chunks retrieved | HMO=%s | tier=%s", len(top_chunks), user_hmo, user_tier)
        return top_chunks

    except Exception as e:
        logger.exception("Failed to get relevant chunks for question: %s", question)
        return []

