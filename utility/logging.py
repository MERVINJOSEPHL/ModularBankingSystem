# utility/logging.py
import logging
import os
from logging.handlers import RotatingFileHandler

# Define the log file path
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "app_activity.log")

# Create log directory if it doesn't exist
os.makedirs(LOG_DIR, exist_ok=True)

# Define log format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

def setup_logger(name):
    """Initializes and returns a logger instance for a given module."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Prevent logs from propagating to the root logger if not needed
    if not logger.handlers:
        # 1. Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(console_handler)

        # 2. File Handler (Rotates the file when it reaches 1MB)
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=1024 * 1024,  # 1 MB
            backupCount=5
        )
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(file_handler)

    return logger