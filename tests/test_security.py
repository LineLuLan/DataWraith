from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import pytest

import datawraith.engine.scenarios.security as security_module
from datawraith.core.shadow_db import ShadowDB
from datawraith.core.types import EventType, SecurityConfig
from datawraith.engine.scenarios.security import SecurityScenario


def pgserver_available() -> bool:
    return importlib.util.find_spec("pgserver") is not None


@pytest.mark.asyncio
async def test_security_scenario_completes_with_fake_db(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    class FakeDB:
        def get_uri(self) -> str:
            return "postgresql://example"

    class FakeConnection:
        async def execute(self, query: str, *args: Any) -> str:
            assert query
            return "OK"

        async def fetchval(self, query: str, *args: Any) -> Any:
            assert query
            if "relrowsecurity" in query:
                return True
            if "count" in query:
                return 0
            if "rolsuper" in query:
                return False
            if "current_user" in query:
                return "datawraith"
            return None

        async def fetch(self, query: str, *args: Any) -> list[dict[str, Any]]:
            assert query
            return []

        async def close(self) -> None:
            return None

    async def fake_connect(uri: str) -> FakeConnection:
        assert uri == "postgresql://example"
        return FakeConnection()

    monkeypatch.setattr(security_module.asyncpg, "connect", fake_connect)
    scenario = SecurityScenario(
        db=FakeDB(),  # type: ignore[arg-type]
        config=SecurityConfig(duration_seconds=10, workers=1, tenants=2, rows_per_tenant=2),
    )

    events = [event async for event in scenario.run()]

    assert scenario.validate_config() == []
    assert events[0].type == EventType.STARTED
    assert events[-1].type == EventType.COMPLETED
    assert events[-1].data is not None
    result = events[-1].data["result"]
    assert result["scenario_type"] == "security"
    assert result["health_score"] == 100


def test_security_scenario_requires_shadow_db() -> None:
    scenario = SecurityScenario(
        db=None,
        config=SecurityConfig(duration_seconds=10, workers=1),
    )

    assert "ShadowDB is required to run security scenario" in scenario.validate_config()


@pytest.mark.asyncio
@pytest.mark.skipif(not pgserver_available(), reason="pgserver unavailable for this Python runtime")
async def test_security_scenario_runs_against_shadow_db(tmp_path: Path) -> None:
    db = ShadowDB(data_dir=tmp_path / "shadow", cleanup_mode="delete")
    db.start()
    try:
        scenario = SecurityScenario(
            db,
            SecurityConfig(duration_seconds=10, workers=1, tenants=2, rows_per_tenant=2),
        )

        events = [event async for event in scenario.run()]

        assert events[-1].type == EventType.COMPLETED
        assert events[-1].data is not None
        assert events[-1].data["result"]["scenario_type"] == "security"
    finally:
        db.stop()
