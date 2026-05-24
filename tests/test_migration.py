from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

import datawraith.engine.scenarios.migration as migration_module
from datawraith.core.shadow_db import ShadowDB
from datawraith.core.types import EventType, MigrationConfig
from datawraith.engine.scenarios.migration import MigrationScenario
from tests.pgserver_support import pgserver_available


@pytest.mark.asyncio
async def test_migration_scenario_completes_with_fake_db(monkeypatch) -> None:  # type: ignore[no-untyped-def]
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

    monkeypatch.setattr(migration_module.asyncpg, "connect", fake_connect)
    scenario = MigrationScenario(
        db=FakeDB(),  # type: ignore[arg-type]
        config=MigrationConfig(
            duration_seconds=10,
            workers=2,
            row_count=10,
            operation_limit=6,
            lock_timeout_ms=500,
        ),
    )

    events = [event async for event in scenario.run()]

    assert scenario.validate_config() == []
    assert events[0].type == EventType.STARTED
    assert events[-1].type == EventType.COMPLETED
    assert events[-1].data is not None
    result = events[-1].data["result"]
    assert result["scenario_type"] == "migration"
    assert result["metrics"]["qps_avg"] > 0


def test_migration_scenario_requires_shadow_db() -> None:
    scenario = MigrationScenario(
        db=None,
        config=MigrationConfig(duration_seconds=10, workers=1, row_count=10),
    )

    assert "ShadowDB is required to run migration scenario" in scenario.validate_config()


def test_migration_sql_builds_safe_operations() -> None:
    add_column = migration_module._migration_sql(
        MigrationConfig(
            duration_seconds=10,
            workers=1,
            target_table="items",
            target_column="flag",
            migration_operation="add_column",
        )
    )
    create_index = migration_module._migration_sql(
        MigrationConfig(
            duration_seconds=10,
            workers=1,
            target_table="items",
            target_column="flag",
            migration_operation="create_index",
        )
    )

    assert 'ALTER TABLE "items" ADD COLUMN IF NOT EXISTS "flag" boolean' == add_column
    assert 'CREATE INDEX IF NOT EXISTS "idx_items_flag" ON "items" ("flag")' == create_index


@pytest.mark.asyncio
@pytest.mark.skipif(not pgserver_available(), reason="pgserver unavailable for this Python runtime")
async def test_migration_scenario_runs_against_shadow_db(tmp_path: Path) -> None:
    db = ShadowDB(data_dir=tmp_path / "shadow", cleanup_mode="delete")
    db.start()
    try:
        scenario = MigrationScenario(
            db,
            MigrationConfig(
                duration_seconds=10,
                workers=2,
                row_count=10,
                operation_limit=20,
            ),
        )

        events = [event async for event in scenario.run()]

        assert events[-1].type == EventType.COMPLETED
        assert events[-1].data is not None
        assert events[-1].data["result"]["scenario_type"] == "migration"
    finally:
        db.stop()
