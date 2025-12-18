import logging
import os
import shutil
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI

from part2.backend.q_and_a_router import q_and_a_router
from part2.backend.user_info_collect_router import user_info_collect_router
from part2.backend.html_loader import preprocess_html
from part2.backend.openai_client import init_client
from part2.backend.logging_config import setup_logging

# ------------------ Helper Functions ------------------
def clear_logs_dir(logs_dir: str = "logs_part2", retries: int = 3, delay: float = 0.5):
    """
    Remove the logs directory if it exists to start fresh logs.
    Retries a few times in case files are locked.
    """
    if os.path.exists(logs_dir):
        # Remove all logging handlers to unlock log files
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
            handler.close()

        for i in range(retries):
            try:
                shutil.rmtree(logs_dir)
                print(f"Removed existing logs directory: {logs_dir}")
                break
            except Exception as e:
                if i < retries - 1:
                    time.sleep(delay)
                else:
                    print(f"Failed to remove {logs_dir}: {e}")


# ------------------ Startup ------------------
clear_logs_dir()          # Clear old logs
setup_logging()  # Configure logging
logger = logging.getLogger(__name__)

# ------------------ Application Lifespan ------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI application lifespan: startup and shutdown tasks."""
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


# ------------------ FastAPI App ------------------
app = FastAPI(
    title="Medical Services Chatbot",
    lifespan=lifespan
)

# Include routers
app.include_router(q_and_a_router)
app.include_router(user_info_collect_router)


# ------------------ Local Development Entrypoint ------------------
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
