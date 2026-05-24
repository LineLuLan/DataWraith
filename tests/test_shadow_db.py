from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from datawraith.core.exceptions import ShadowDBError
from datawraith.core.shadow_db import ShadowDB


def pgserver_available() -> bool:
    return importlib.util.find_spec("pgserver") is not None


def test_shadow_db_rejects_invalid_cleanup_mode() -> None:
    with pytest.raises(ShadowDBError, match="cleanup_mode"):
        ShadowDB(cleanup_mode="wipe")


def test_shadow_db_get_uri_requires_start() -> None:
    db = ShadowDB()

    with pytest.raises(ShadowDBError, match="not started"):
        db.get_uri()


@pytest.mark.skipif(not pgserver_available(), reason="pgserver unavailable for this Python runtime")
def test_shadow_db_loads_schema_and_lists_tables(tmp_path: Path) -> None:
    db = ShadowDB(data_dir=tmp_path / "shadow", cleanup_mode="delete")
    db.start()
    try:
        import asyncio

        asyncio.run(
            db.load_schema(
                """
                CREATE TABLE products (
                    id integer PRIMARY KEY,
                    name text NOT NULL
                );
                """
            )
        )
        assert db.list_tables() == ["products"]
    finally:
        db.stop()
