import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from part2.backend.q_and_a_router import q_and_a_router
from part2.backend.user_info_collect_router import user_info_collect_router
from html_loader import preprocess_html
from openai_client import init_client
import logging_config as log_conf

# ---------------------------------------------------
# Logging setup
# ---------------------------------------------------
log_conf.setup_logging()  # configure root logging first
logger = logging.getLogger(__name__)  # use module name instead of "backend"

# --------------------------------------------------
# Application lifespan
# ---------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting backend initialization")

    # Initialize Azure OpenAI client
    try:
        app.state.azure_client = init_client()
        logger.info("AzureOpenAI client initialized successfully")
    except Exception:
        logger.exception("Failed to initialize AzureOpenAI client")
        raise RuntimeError("Startup failed: AzureOpenAI client could not be initialized")

    # Preprocess HTMLs and create embeddings
    try:
        logger.info("Starting HTML preprocessing and embedding generation")
        app.state.all_chunks = preprocess_html(client=app.state.azure_client)
        logger.info(
            "HTML preprocessing completed successfully. Loaded %d chunks",
            len(app.state.all_chunks)
        )
    except FileNotFoundError as e:
        logger.error("HTML data directory not found: %s", e)
        raise RuntimeError("Startup failed: HTML data directory missing")
    except Exception:
        logger.exception("Unexpected error during HTML preprocessing")
        raise RuntimeError("Startup failed: HTML preprocessing error")

    logger.info("Backend startup completed successfully")
    yield

    # Shutdown
    logger.info("Backend shutting down")
    logger.info("Backend shutdown completed")

# ---------------------------------------------------
# FastAPI app
# ---------------------------------------------------
app = FastAPI(
    title="Medical Services Chatbot",
    lifespan=lifespan
)

app.include_router(q_and_a_router)
app.include_router(user_info_collect_router)

# ---------------------------------------------------
# Local development entrypoint
# ---------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    logger.info("Starting Uvicorn server")
    uvicorn.run(
        "backend_main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
