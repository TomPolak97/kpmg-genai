import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()  # optionally: load_dotenv(dotenv_path="path/to/.env")

# Azure Document Intelligence
DOC_INTEL_ENDPOINT = os.getenv("DOC_INTEL_ENDPOINT")
DOC_INTEL_KEY = os.getenv("DOC_INTEL_KEY")

if not DOC_INTEL_ENDPOINT or not DOC_INTEL_KEY:
    raise ValueError("Document Intelligence environment variables are not set")

# Azure OpenAI
AOAI_ENDPOINT = os.getenv("AOAI_ENDPOINT")
AOAI_KEY = os.getenv("AOAI_KEY")
AOAI_DEPLOYMENT = os.getenv("AOAI_DEPLOYMENT", "gpt-4o")

if not AOAI_ENDPOINT or not AOAI_KEY:
    raise ValueError("Azure OpenAI environment variables are not set")
