"""Helpers for real local PostgreSQL E2E tests."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import psycopg
import pytest

from datawraith.core.database_url import validate_local_database_url

E2E_TABLES = [
    "dw_security_records",
    "dw_security_users",
    "dw_security_tenants",
    "dw_orders",
    "dw_products",
    "dw_customers",
    "dw_migration_items",
    "products",
]


def pgserver_available() -> bool:
    return importlib.util.find_spec("pgserver") is not None


def runtime_args(tmp_path: Path) -> list[str]:
    database_url = local_database_url()
    if database_url is not None:
        reset_local_database(database_url)
        return ["--database-url", database_url]

    if pgserver_available():
        return ["--data-dir", str(tmp_path / "shadow")]

    pytest.skip(
        "real DB runtime unavailable; install Python 3.12 + pgserver or set "
        "DATAWRAITH_E2E_DATABASE_URL / DATAWRAITH_DATABASE_URL to localhost PostgreSQL"
    )


def local_database_url() -> str | None:
    database_url = os.getenv("DATAWRAITH_E2E_DATABASE_URL") or os.getenv(
        "DATAWRAITH_DATABASE_URL"
    )
    if database_url is None:
        return None
    return validate_local_database_url(database_url)


def reset_local_database(database_url: str) -> None:
    """Reset known DataWraith E2E tables in a guarded local test database."""
    table_list = ", ".join(f'"{table}"' for table in E2E_TABLES)
    with psycopg.connect(database_url, autocommit=True, connect_timeout=5) as conn:
        conn.execute(f"DROP TABLE IF EXISTS {table_list} CASCADE")
