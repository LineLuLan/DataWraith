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


def test_shadow_db_rejects_nonlocal_external_url() -> None:
    with pytest.raises(ShadowDBError, match="only accepts local"):
        ShadowDB(external_url="postgresql://db.example.com/prod")


def test_shadow_db_uses_external_local_url(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    calls: list[str] = []

    class FakeConnection:
        def __enter__(self):  # type: ignore[no-untyped-def]
            calls.append("enter")
            return self

        def __exit__(self, exc_type, exc, traceback):  # type: ignore[no-untyped-def]
            calls.append("exit")

        def execute(self, sql: str) -> None:
            calls.append(sql)

    def fake_connect(uri: str, connect_timeout: int = 0):  # type: ignore[no-untyped-def]
        calls.append(f"connect:{uri}:{connect_timeout}")
        return FakeConnection()

    monkeypatch.setattr("datawraith.core.shadow_db.psycopg.connect", fake_connect)

    db = ShadowDB(external_url="postgresql://localhost/datawraith")
    assert db.start() == "postgresql://localhost/datawraith"
    assert db.get_uri() == "postgresql://localhost/datawraith"
    db.stop()

    assert calls == [
        "connect:postgresql://localhost/datawraith:5",
        "enter",
        "SELECT 1",
        "exit",
    ]
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
