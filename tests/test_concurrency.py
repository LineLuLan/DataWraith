from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path

import pytest

from datawraith.core.shadow_db import ShadowDB
from datawraith.core.types import ConcurrencyConfig, EventType
from datawraith.engine.scenarios.concurrency import ConcurrencyScenario
from datawraith.engine.seeder import SeedPlan, execute_seed_plan, parse_column_specs


def pgserver_available() -> bool:
    return importlib.util.find_spec("pgserver") is not None


@pytest.mark.asyncio
@pytest.mark.skipif(not pgserver_available(), reason="pgserver unavailable for this Python runtime")
async def test_concurrency_scenario_runs_against_shadow_db(tmp_path: Path) -> None:
    db = ShadowDB(data_dir=tmp_path / "shadow", cleanup_mode="delete")
    db.start()
    try:
        await db.load_schema(
            """
            CREATE TABLE products (
                id integer PRIMARY KEY,
                name text NOT NULL,
                stock integer NOT NULL
            );
            """
        )
        await asyncio.to_thread(
            execute_seed_plan,
            db,
            SeedPlan(
                table="products",
                rows=5,
                columns=parse_column_specs(["id:int", "name:name", "stock:int"]),
            ),
        )
        scenario = ConcurrencyScenario(
            db,
            ConcurrencyConfig(
                duration_seconds=10,
                workers=2,
                concurrent_updates=10,
                target_table="products",
                target_column="stock",
            ),
        )

        events = [event async for event in scenario.run()]

        assert events[-1].type == EventType.COMPLETED
        assert events[-1].data is not None
        assert events[-1].data["result"]["metrics"]["qps_avg"] > 0
    finally:
        db.stop()
