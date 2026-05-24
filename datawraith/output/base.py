"""Output exporter contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from datawraith.core.types import ScenarioResult


class Exporter(ABC):
    """Base exporter contract."""

    format: str
    extension: str

    @abstractmethod
    def export(self, result: ScenarioResult, output_path: Path) -> None:
        """Export a scenario result."""
        raise NotImplementedError
