"""Scenario orchestration helpers."""

from __future__ import annotations

from collections.abc import AsyncIterator

from datawraith.core.exceptions import ConfigError
from datawraith.core.shadow_db import ShadowDB
from datawraith.core.types import ScenarioConfig, ScenarioEvent
from datawraith.engine.scenarios import get_scenario


async def run_scenario(
    scenario_name: str,
    config: ScenarioConfig,
    db: ShadowDB | None = None,
) -> AsyncIterator[ScenarioEvent]:
    """Run a registered scenario and yield its events."""
    owns_db = db is None
    active_db = db or ShadowDB(cleanup_mode="delete")
    if owns_db:
        active_db.start()

    scenario_cls = get_scenario(scenario_name)
    scenario = scenario_cls(active_db, config)
    errors = scenario.validate_config()
    if errors:
        if owns_db:
            active_db.stop()
        raise ConfigError(errors)

    try:
        async for event in scenario.run():
            yield event
    finally:
        if owns_db:
            active_db.stop()
