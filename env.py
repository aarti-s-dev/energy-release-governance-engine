from __future__ import annotations

import os
from typing import Iterable

from arge.logging_config import configure_logging


logger = configure_logging("arge.env")


def env_vars_present(names: Iterable[str]) -> bool:
    """Return True when all environment variables are populated.

    Args:
        names: Environment variable names that must be present.

    Returns:
        bool: True when every variable is set to a non-empty value.
    """
    return all(bool(os.getenv(name)) for name in names)


def log_mock_mode(missing_names: Iterable[str]) -> None:
    """Emit a standard mock-mode message for recruiter-friendly demos.

    Args:
        missing_names: Environment variable names that were not found.
    """
    missing = ", ".join(sorted(set(missing_names)))
    logger.info(
        "Environment variables missing: Running in Mock Mode for demonstration. Missing=%s",
        missing or "none",
    )
