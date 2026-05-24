"""Base scenario contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from datawraith.core.shadow_db import ShadowDB
from datawraith.core.types import ScenarioConfig, ScenarioEvent


class Scenario(ABC):
    """Abstract base class for all chaos test scenarios."""

    name: str
    display_name: str

    def __init__(self, db: ShadowDB | None, config: ScenarioConfig) -> None:
        self.db = db
        self.config = config

    @abstractmethod
    def run(self) -> AsyncIterator[ScenarioEvent]:
        """Execute the scenario and stream events in real time."""
        raise NotImplementedError

    @abstractmethod
    def validate_config(self) -> list[str]:
        """Validate the scenario config. Empty list means valid."""
        raise NotImplementedError
