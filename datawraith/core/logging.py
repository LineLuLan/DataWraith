"""Logging setup for DataWraith."""

from __future__ import annotations

import logging
from pathlib import Path

from rich.logging import RichHandler


def setup_logging(level: str = "INFO", log_file: Path | None = None) -> None:
    """Configure local-only logging."""
    handlers: list[logging.Handler] = [RichHandler(rich_tracebacks=True)]
    if log_file is not None:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=handlers,
        force=True,
    )
