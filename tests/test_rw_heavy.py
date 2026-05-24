from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

import datawraith.engine.scenarios.rw_heavy as rw_heavy_module
from datawraith.core.shadow_db import ShadowDB
from datawraith.core.types import EventType, RWHeavyConfig
from datawraith.engine.scenarios.rw_heavy import RWHeavyScenario
from tests.pgserver_support import pgserver_available


@pytest.mark.asyncio
async def test_rw_heavy_scenario_completes_with_fake_db(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    class FakeDB:
        def get_uri(self) -> str:
            return "postgresql://example"

    class FakeConnection:
        async def execute(self, query: str, *args: Any) -> str:
            assert query
            return "OK"

        async def fetch(self, query: str, *args: Any) -> list[dict[str, Any]]:
            assert query
            return []

        async def close(self) -> None:
            return None

    async def fake_connect(uri: str) -> FakeConnection:
        assert uri == "postgresql://example"
        return FakeConnection()

    monkeypatch.setattr(rw_heavy_module.asyncpg, "connect", fake_connect)
    scenario = RWHeavyScenario(
        db=FakeDB(),  # type: ignore[arg-type]
        config=RWHeavyConfig(
            duration_seconds=10,
            workers=2,
            read_write_ratio=0.5,
            row_count=10,
            operation_limit=6,
            slow_query_threshold_ms=1.0,
        ),
    )

    events = [event async for event in scenario.run()]

    assert scenario.validate_config() == []
    assert events[0].type == EventType.STARTED
    assert events[-1].type == EventType.COMPLETED
    assert events[-1].data is not None
    result = events[-1].data["result"]
    assert result["scenario_type"] == "rw_heavy"
    assert result["metrics"]["qps_avg"] > 0


def test_rw_heavy_scenario_requires_shadow_db() -> None:
    scenario = RWHeavyScenario(
        db=None,
        config=RWHeavyConfig(duration_seconds=10, workers=1, row_count=10),
    )

    assert "ShadowDB is required to run rw-heavy scenario" in scenario.validate_config()


def test_rw_heavy_operation_builder_covers_read_update_insert() -> None:
    config = RWHeavyConfig(
        duration_seconds=10,
        workers=1,
        read_write_ratio=0.5,
        row_count=10,
    )

    read_label, read_query, read_args = rw_heavy_module._operation_for(0, config)
    update_label, update_query, update_args = rw_heavy_module._operation_for(50, config)
    insert_label, insert_query, insert_args = rw_heavy_module._operation_for(51, config)

    assert read_label == "read"
    assert "JOIN" in read_query
    assert read_args == (1, 10)
    assert update_label == "update"
    assert "UPDATE" in update_query
    assert update_args == (1,)
    assert insert_label == "insert"
    assert "INSERT INTO" in insert_query
    assert len(insert_args) == 3


@pytest.mark.asyncio
@pytest.mark.skipif(not pgserver_available(), reason="pgserver unavailable for this Python runtime")
async def test_rw_heavy_scenario_runs_against_shadow_db(tmp_path: Path) -> None:
    db = ShadowDB(data_dir=tmp_path / "shadow", cleanup_mode="delete")
    db.start()
    try:
        scenario = RWHeavyScenario(
            db,
            RWHeavyConfig(
                duration_seconds=10,
                workers=2,
                row_count=10,
                operation_limit=20,
                slow_query_threshold_ms=50.0,
            ),
        )

        events = [event async for event in scenario.run()]

        assert events[-1].type == EventType.COMPLETED
        assert events[-1].data is not None
        assert events[-1].data["result"]["metrics"]["qps_avg"] > 0
    finally:
        db.stop()
