from __future__ import annotations

import logging
import os
import sys


LOG_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_logging(name: str) -> logging.Logger:
    """Create a consistently formatted logger for CLI and GitHub Actions output."""
    level_name = os.getenv("ARGE_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    logger = logging.getLogger(name)
    if logger.handlers:
        logger.setLevel(level)
        return logger

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt=LOG_FORMAT,
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
    return logger
