from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path

import pytest

from datawraith.core.shadow_db import ShadowDB
from datawraith.engine.seeder import SeedPlan, execute_seed_plan, parse_column_specs


def pgserver_available() -> bool:
    return importlib.util.find_spec("pgserver") is not None


@pytest.mark.skipif(not pgserver_available(), reason="pgserver unavailable for this Python runtime")
def test_execute_seed_plan_inserts_rows_into_shadow_db(tmp_path: Path) -> None:
    db = ShadowDB(data_dir=tmp_path / "shadow", cleanup_mode="delete")
    db.start()
    try:
        asyncio.run(
            db.load_schema(
                """
                CREATE TABLE products (
                    id integer PRIMARY KEY,
                    name text NOT NULL,
                    stock integer NOT NULL
                );
                """
            )
        )
        result = execute_seed_plan(
            db,
            SeedPlan(
                table="products",
                rows=3,
                columns=parse_column_specs(["id:int", "name:name", "stock:int"]),
            ),
        )

        with db.sync_connection() as conn:
            count = conn.execute("SELECT count(*) FROM products").fetchone()

        assert result.rows_inserted == 3
        assert count is not None
        assert count[0] == 3
    finally:
        db.stop()
