"""Application settings."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Local DataWraith settings."""

    model_config = SettingsConfigDict(env_prefix="DATAWRAITH_", extra="ignore")

    home_dir: Path = Field(default_factory=lambda: Path.home() / ".datawraith")
    workspace_dir: Path = Field(default_factory=lambda: Path.cwd() / ".datawraith")
    log_level: str = "INFO"
    telemetry_enabled: bool = False
    database_url: str | None = None

    @property
    def shadow_data_dir(self) -> Path:
        """Default local shadow PostgreSQL data directory."""
        return self.workspace_dir / "shadow"


def get_settings() -> Settings:
    """Return current settings."""
    return Settings()
