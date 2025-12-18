import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logging(level=logging.INFO, logs_dir="logs_part2", log_file="part2_app_front.log"):
    """
    Configure root logging for the application.
    Logs are written only to a rotating log file in `logs_dir`.
    Returns the root logger.
    """
    # Ensure logs directory exists
    os.makedirs(logs_dir, exist_ok=True)
    log_path = os.path.join(logs_dir, log_file)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=5_000_000,  # 5 MB
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    root_logger.addHandler(file_handler)
    root_logger.info("Logging initialized. Log file: %s", log_path)

    return root_logger  # <-- add this!
