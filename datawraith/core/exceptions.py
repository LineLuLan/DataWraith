"""Custom exception hierarchy for DataWraith."""

from __future__ import annotations


class DataWraithError(Exception):
    """Base class for all DataWraith errors."""


class ShadowDBError(DataWraithError):
    """Embedded PostgreSQL or pgserver issue."""


class SchemaError(DataWraithError):
    """Schema parsing or loading issue."""


class SeederError(DataWraithError):
    """Synthetic data generation issue."""


class ScenarioError(DataWraithError):
    """Scenario execution issue."""


class ConfigError(DataWraithError):
    """Invalid user or scenario configuration."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("\n".join(errors))


class AIBridgeError(DataWraithError):
    """AI provider issue for Phase 3+."""
