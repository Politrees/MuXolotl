"""Logging utilities for MuXolotl"""

import logging
import os
from datetime import datetime


def setup_logger(name="MuXolotl", level=logging.INFO):
    """Setup application logger

    Args:
        name: Logger name
        level: Logging level

    Returns:
        Logger instance

    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Console handler - only warnings and errors
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)  # Changed from INFO to WARNING

    # File handler - all info
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"muxolotl_{datetime.now().strftime('%Y%m%d')}.log")
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


def get_logger(name="MuXolotl"):
    """Get existing logger instance"""
    return logging.getLogger(name)
