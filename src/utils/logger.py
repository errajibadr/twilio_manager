import logging
import os
import sys
from pathlib import Path
from typing import Optional


def get_log_path():
    # If LOG_PATH environment variable is set (in Docker), use it
    if os.getenv("LOG_PATH"):
        base_path = Path(os.environ["LOG_PATH"])
    else:
        # For local development, use the project root/logs directory
        base_path = Path(__file__).parent.parent.parent / "logs"

    # Create the directory if it doesn't exist
    base_path.mkdir(parents=True, exist_ok=True)
    return base_path


def setup_logger(name: str, log_file: Optional[Path] = None, level=logging.INFO) -> logging.Logger:
    """Set up logger with console and file handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Create formatters
    detailed_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(detailed_formatter)
    logger.addHandler(console_handler)

    # Add file handler if log_file is provided
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)

    return logger
