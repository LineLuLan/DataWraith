"""Scenario registry."""

from __future__ import annotations

from datawraith.engine.scenarios.base import Scenario
from datawraith.engine.scenarios.concurrency import ConcurrencyScenario

SCENARIO_REGISTRY: dict[str, type[Scenario]] = {
    ConcurrencyScenario.name: ConcurrencyScenario,
}


def get_scenario(name: str) -> type[Scenario]:
    """Return a scenario class by registry name."""
    try:
        return SCENARIO_REGISTRY[name]
    except KeyError as exc:
        available = ", ".join(sorted(SCENARIO_REGISTRY))
        raise ValueError(f"Unknown scenario '{name}'. Available: {available}") from exc
