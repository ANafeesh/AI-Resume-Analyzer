"""Utility functions for logging, path management, and text normalization."""

from __future__ import annotations

import logging
import re
import sys
from pathlib import Path

_LOG_FORMAT = "%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"
_LOGGER: logging.Logger | None = None


def get_project_root() -> Path:
    """Return the absolute path to the project root directory.

    Returns:
        Path: Project root directory path.
    """
    return Path(__file__).resolve().parent.parent


def get_logger(name: str = "resume_analyzer") -> logging.Logger:
    """Configure and return a standardized logger instance.

    Args:
        name: Name for the logger instance.

    Returns:
        logging.Logger: Configured logger.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(_LOG_FORMAT))
        logger.addHandler(handler)
        logger.propagate = False
    return logger


def clean_text(raw_text: str | None) -> str:
    """Normalize whitespace and strip unprintable characters while preserving line structure.

    Args:
        raw_text: The input text to clean.

    Returns:
        str: Cleaned, readable text string.
    """
    if not raw_text:
        return ""

    # Replace null bytes, special control chars (except standard whitespace \t, \n, \r)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", " ", raw_text)

    # Normalize various unicode spaces (e.g. non-breaking space, thin space) to standard space
    text = re.sub(r"[\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]", " ", text)

    # Normalize carriage returns to newlines
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Collapse multiple inline spaces while keeping newlines
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]

    # Remove excessive blank lines (more than 2 consecutive newlines)
    cleaned_lines: list[str] = []
    blank_count = 0
    for line in lines:
        if not line:
            blank_count += 1
            if blank_count <= 1:
                cleaned_lines.append("")
        else:
            blank_count = 0
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()
