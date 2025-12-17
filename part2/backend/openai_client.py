import os
import logging
from dotenv import load_dotenv
from openai import AzureOpenAI

# Load environment variables from .env file
load_dotenv()  # optionally, pass path: load_dotenv(dotenv_path="path/to/.env")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_client() -> AzureOpenAI:
    """
    Initialize and return AzureOpenAI client using environment variables.
    Raises RuntimeError if configuration is invalid.
    """
    try:
        # Read secrets from environment
        endpoint = os.getenv("AOAI_ENDPOINT_PART2")
        api_key = os.getenv("AOAI_KEY_PART2")
        api_version = os.getenv("AOAI_API_VERSION_PART2", "2024-02-15-preview")

        # Validate environment variables
        if not endpoint:
            raise ValueError("AOAI_ENDPOINT_PART2 is not set in environment variables")

        if not api_key:
            raise ValueError("AOAI_KEY_PART2 is not set in environment variables")

        logger.info("Initializing Azure OpenAI client")
        logger.debug(
            "Azure OpenAI config | endpoint=%s | api_version=%s",
            endpoint,
            api_version
        )

        # Initialize client
        client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version
        )

        return client

    except Exception as e:
        logger.exception("Failed to initialize Azure OpenAI client")
        raise RuntimeError("Azure OpenAI client initialization failed") from e

