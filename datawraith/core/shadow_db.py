"""Embedded PostgreSQL wrapper using pgserver."""

from __future__ import annotations

import importlib
import logging
import shutil
import tempfile
from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path
from typing import Any

import psycopg

from datawraith.core.database_url import validate_local_database_url
from datawraith.core.exceptions import ShadowDBError

logger = logging.getLogger(__name__)


class ShadowDB:
    """Embedded PostgreSQL instance for chaos testing.

    `pgserver` is imported lazily so CLI and contract tests remain usable on
    Python versions where upstream pgserver wheels are not available yet.
    When `external_url` is provided, ShadowDB connects to a user-managed local
    PostgreSQL instance instead of starting embedded pgserver.
    """

    def __init__(
        self,
        data_dir: Path | None = None,
        cleanup_mode: str = "stop",
        external_url: str | None = None,
    ) -> None:
        if cleanup_mode not in {"stop", "delete"}:
            raise ShadowDBError("cleanup_mode must be 'stop' or 'delete'")

        self._external_url = (
            validate_local_database_url(external_url) if external_url is not None else None
        )
        self._owns_data_dir = data_dir is None
        self._data_dir = data_dir or Path(tempfile.mkdtemp(prefix="datawraith_"))
        self._cleanup_mode = cleanup_mode
        self._server: Any | None = None
        self._uri: str | None = None

    def start(self) -> str:
        """Start embedded PostgreSQL or validate an external local URI."""
        if self._external_url is not None:
            try:
                with psycopg.connect(self._external_url, connect_timeout=5) as conn:
                    conn.execute("SELECT 1")
            except psycopg.Error as exc:
                raise ShadowDBError(f"Failed to connect to local PostgreSQL: {exc}") from exc
            self._uri = self._external_url
            return self._uri

        try:
            pgserver = importlib.import_module("pgserver")
        except ModuleNotFoundError as exc:
            raise ShadowDBError(
                "pgserver is not installed for this Python runtime. Use Python 3.12 "
                "for embedded PostgreSQL, or pass --database-url / set "
                "DATAWRAITH_DATABASE_URL to a local PostgreSQL instance."
            ) from exc

        try:
            self._server = pgserver.get_server(self._data_dir, cleanup_mode=self._cleanup_mode)
            self._uri = str(self._server.get_uri())
            with psycopg.connect(self._uri, connect_timeout=5) as conn:
                conn.execute("SELECT 1")
        except (OSError, RuntimeError, psycopg.Error) as exc:
            raise ShadowDBError(f"Failed to start shadow DB: {exc}") from exc

        return self._uri

    def stop(self) -> None:
        """Stop PostgreSQL and remove owned temp data when configured."""
        if self._external_url is not None:
            self._uri = None
            return

        if self._server is not None:
            try:
                self._server.cleanup()
            except (OSError, RuntimeError) as exc:
                logger.debug("Shadow DB cleanup failed: %s", exc)
            finally:
                self._server = None
                self._uri = None

        if self._cleanup_mode == "delete" and self._owns_data_dir and self._data_dir.exists():
            shutil.rmtree(self._data_dir, ignore_errors=True)

    def get_uri(self) -> str:
        """Return the active PostgreSQL URI."""
        if self._uri is None:
            raise ShadowDBError("Shadow DB is not started. Call start() first.")
        return self._uri

    @contextmanager
    def sync_connection(self) -> Generator[psycopg.Connection[Any], None, None]:
        """Yield a sync psycopg connection."""
        with psycopg.connect(self.get_uri()) as conn:
            yield conn

    @asynccontextmanager
    async def connection(self) -> AsyncGenerator[psycopg.AsyncConnection[Any], None]:
        """Yield an async psycopg connection."""
        async with await psycopg.AsyncConnection.connect(self.get_uri()) as conn:
            yield conn

    async def load_schema(self, sql: str) -> None:
        """Execute DDL against the shadow DB."""
        async with self.connection() as conn:
            await conn.execute(sql)

    def list_tables(self) -> list[str]:
        """List user tables visible in the public schema.

        This helper is intentionally narrow for Phase 1 CLI verification. It
        avoids PostgreSQL system schemas and keeps the return value stable for
        tests and user-facing summaries.
        """
        query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """
        with self.sync_connection() as conn:
            rows = conn.execute(query).fetchall()
        return [str(row[0]) for row in rows]

    async def enable_extension(self, name: str) -> None:
        """Enable a PostgreSQL extension by simple identifier name."""
        if not name.replace("_", "").isalnum():
            raise ShadowDBError(f"Invalid extension name: {name}")

        async with self.connection() as conn:
            await conn.execute(f"CREATE EXTENSION IF NOT EXISTS {name}")

    def __enter__(self) -> ShadowDB:
        self.start()
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.stop()
