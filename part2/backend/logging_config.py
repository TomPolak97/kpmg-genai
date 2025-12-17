import logging
import sys

def setup_logging(level=logging.INFO):
    """
    Configure root logging for the application.
    Call this once at app startup.
    """
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    # Stream to stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Avoid adding multiple handlers
    if not root_logger.handlers:
        root_logger.addHandler(handler)
