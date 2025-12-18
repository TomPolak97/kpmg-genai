import os
import logging
from logging.handlers import RotatingFileHandler

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

def setup_logging():
    logger = logging.getLogger()
    if logger.handlers:
        return  # Prevent duplicate handlers

    logger.setLevel(logging.getLevelName(LOG_LEVEL))
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    # Ensure logs directory exists
    os.makedirs("logs_part1", exist_ok=True)

    # File-only handler (rotates automatically)
    file_handler = RotatingFileHandler(
        "logs_part1/part1_app.log",  # log file path inside logs_part1
        maxBytes=5_000_000,
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
