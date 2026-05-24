"""Phase 3 migration-lock scenario."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from datetime import datetime
from statistics import quantiles
from time import perf_counter

import asyncpg

from datawraith.core.shadow_db import ShadowDB
from datawraith.core.types import (
    EventType,
    HealthMetrics,
    MigrationConfig,
    ScenarioEvent,
    ScenarioResult,
    ScenarioType,
)
from datawraith.engine.migration_analysis import (
    MigrationObservation,
    culprits_for_migration,
)
from datawraith.engine.scenarios.base import Scenario
from datawraith.engine.seeder import quote_identifier


class MigrationScenario(Scenario):
    """Run workload while applying a safe local DDL migration."""

    name = "migration"
    display_name = "Migration Lock"

    def __init__(self, db: ShadowDB | None, config: MigrationConfig) -> None:
        super().__init__(db, config)
        self.config: MigrationConfig = config

    def validate_config(self) -> list[str]:
        errors: list[str] = []
        if self.db is None:
            errors.append("ShadowDB is required to run migration scenario")
        for identifier in (self.config.target_table, self.config.target_column):
            if "\x00" in identifier:
                errors.append("Migration identifiers cannot contain NUL bytes")
        return errors

    async def run(self) -> AsyncIterator[ScenarioEvent]:
        started_at = datetime.now()
        yield ScenarioEvent(
            type=EventType.STARTED,
            message=f"Starting migration-lock scenario: {self.config.migration_operation}",
        )

        stats = _MigrationStats()
        logs: list[str] = []
        migration_duration_ms = 0.0
        migration_sql = ""
        worker_tasks: list[asyncio.Task[None]] = []
        reporter_task: asyncio.Task[None] | None = None
        event_queue: asyncio.Queue[ScenarioEvent] = asyncio.Queue()
        started_perf = perf_counter()

        try:
            if self.db is None:
                raise RuntimeError("ShadowDB is required to run migration scenario")
            uri = self.db.get_uri()
            await _prepare_table(uri, self.config)
            yield ScenarioEvent(
                type=EventType.LOG,
                message=f"Prepared {self.config.row_count} rows in {self.config.target_table}",
            )

            deadline = perf_counter() + self.config.duration_seconds
            for worker_id in range(self.config.workers):
                worker_tasks.append(
                    asyncio.create_task(
                        _workload_worker(
                            worker_id=worker_id,
                            uri=uri,
                            config=self.config,
                            deadline=deadline,
                            stats=stats,
                            logs=logs,
                        )
                    )
                )
            reporter_task = asyncio.create_task(
                _report_metrics(event_queue, stats, started_perf, deadline)
            )

            await asyncio.sleep(0.25)
            migration_sql = _migration_sql(self.config)
            migration_started = perf_counter()
            await _execute_migration(uri, migration_sql, self.config)
            migration_duration_ms = (perf_counter() - migration_started) * 1000
            yield ScenarioEvent(
                type=EventType.LOG,
                message=f"Migration completed in {migration_duration_ms:.1f}ms",
                data={"migration_sql": migration_sql},
            )

            pending = set(worker_tasks)
            while pending:
                done, pending = await asyncio.wait(
                    pending,
                    timeout=0.25,
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for task in done:
                    task.result()
                while not event_queue.empty():
                    yield event_queue.get_nowait()
        except (asyncpg.PostgresError, OSError, RuntimeError) as exc:
            stats.errors += 1
            message = f"Migration scenario failed: {exc}"
            logs.append(message)
            yield ScenarioEvent(type=EventType.ERROR, message=message)
        finally:
            for task in worker_tasks:
                if not task.done():
                    task.cancel()
            if worker_tasks:
                await asyncio.gather(*worker_tasks, return_exceptions=True)
            if reporter_task is not None:
                reporter_task.cancel()
                await asyncio.gather(reporter_task, return_exceptions=True)

        completed_at = datetime.now()
        duration_seconds = max((completed_at - started_at).total_seconds(), 0.001)
        observation = MigrationObservation(
            operation=migration_sql or self.config.migration_operation,
            lock_timeout_ms=self.config.lock_timeout_ms,
            migration_duration_ms=migration_duration_ms,
            blocked_operations=stats.lock_timeouts,
            error_count=stats.errors,
        )
        result = ScenarioResult(
            scenario_name=self.name,
            scenario_type=ScenarioType.MIGRATION,
            config=self.config.model_dump(mode="json"),
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=duration_seconds,
            health_score=_health_score(stats, migration_duration_ms, self.config),
            metrics=HealthMetrics(
                qps_max=stats.qps_max,
                qps_avg=stats.completed / duration_seconds,
                latency_p50_ms=_percentile(stats.latencies_ms, 0.50),
                latency_p95_ms=_percentile(stats.latencies_ms, 0.95),
                latency_p99_ms=_percentile(stats.latencies_ms, 0.99),
                error_count=stats.errors,
                error_rate=stats.errors / max(stats.completed + stats.errors, 1),
                lock_wait_ms_total=max(0.0, migration_duration_ms - self.config.lock_timeout_ms),
            ),
            top_culprits=culprits_for_migration(observation),
            raw_logs=logs[-100:],
        )
        yield ScenarioEvent(
            type=EventType.COMPLETED,
            message="Migration scenario completed.",
            data={"result": result.model_dump(mode="json")},
        )


class _MigrationStats:
    """Mutable stats shared by migration workers."""

    def __init__(self) -> None:
        self.completed = 0
        self.errors = 0
        self.lock_timeouts = 0
        self.latencies_ms: list[float] = []
        self.qps_max = 0.0


async def _prepare_table(uri: str, config: MigrationConfig) -> None:
    table = quote_identifier(config.target_table)
    conn = await asyncpg.connect(uri)
    try:
        await conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {table} (
                id integer PRIMARY KEY,
                name text NOT NULL,
                status text NOT NULL,
                updated_at timestamptz NOT NULL DEFAULT now()
            )
            """
        )
        await conn.execute(
            f"""
            INSERT INTO {table} (id, name, status, updated_at)
            SELECT id, 'Item ' || id, 'active', now()
            FROM generate_series(1, $1) AS id
            ON CONFLICT (id) DO NOTHING
            """,
            config.row_count,
        )
        if config.migration_operation == "create_index":
            await conn.execute(
                f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS "
                f"{quote_identifier(config.target_column)} boolean DEFAULT false"
            )
    finally:
        await conn.close()


async def _execute_migration(uri: str, sql: str, config: MigrationConfig) -> None:
    conn = await asyncpg.connect(uri)
    try:
        await conn.execute(f"SET lock_timeout = '{config.lock_timeout_ms}ms'")
        await conn.execute(f"SET statement_timeout = '{config.statement_timeout_ms}ms'")
        if config.hold_lock_ms > 0:
            await conn.execute("BEGIN")
            try:
                await conn.execute(
                    f"LOCK TABLE {quote_identifier(config.target_table)} IN ACCESS EXCLUSIVE MODE"
                )
                await asyncio.sleep(config.hold_lock_ms / 1000)
                await conn.execute(sql)
                await conn.execute("COMMIT")
            except BaseException:
                await conn.execute("ROLLBACK")
                raise
            return
        await conn.execute(sql)
    finally:
        await conn.close()


async def _workload_worker(
    *,
    worker_id: int,
    uri: str,
    config: MigrationConfig,
    deadline: float,
    stats: _MigrationStats,
    logs: list[str],
) -> None:
    conn = await asyncpg.connect(uri)
    table = quote_identifier(config.target_table)
    try:
        operation = worker_id
        while perf_counter() < deadline and stats.completed < config.operation_limit:
            row_id = (operation % config.row_count) + 1
            query = (
                f"UPDATE {table} SET updated_at = now(), status = 'active' "
                "WHERE id = $1"
                if operation % 3 == 0
                else f"SELECT id, status FROM {table} WHERE id = $1"
            )
            started = perf_counter()
            try:
                if query.startswith("SELECT"):
                    await conn.fetch(query, row_id)
                else:
                    await conn.execute(query, row_id)
                stats.completed += 1
                stats.latencies_ms.append((perf_counter() - started) * 1000)
            except (asyncpg.exceptions.LockNotAvailableError, asyncpg.exceptions.QueryCanceledError) as exc:
                stats.lock_timeouts += 1
                stats.errors += 1
                logs.append(f"worker={worker_id} lock timeout/cancel: {exc}")
            except asyncpg.PostgresError as exc:
                stats.errors += 1
                logs.append(f"worker={worker_id} postgres error: {exc}")
            operation += config.workers
    finally:
        await conn.close()


async def _report_metrics(
    queue: asyncio.Queue[ScenarioEvent],
    stats: _MigrationStats,
    started_perf: float,
    deadline: float,
) -> None:
    previous_completed = 0
    previous_time = started_perf
    while perf_counter() < deadline:
        await asyncio.sleep(1)
        now = perf_counter()
        elapsed = max(now - previous_time, 0.001)
        qps = (stats.completed - previous_completed) / elapsed
        stats.qps_max = max(stats.qps_max, qps)
        previous_completed = stats.completed
        previous_time = now
        await queue.put(
            ScenarioEvent(
                type=EventType.METRIC,
                message="Migration metrics update",
                data={
                    "completed": stats.completed,
                    "errors": stats.errors,
                    "lock_timeouts": stats.lock_timeouts,
                    "qps": qps,
                },
            )
        )


def _migration_sql(config: MigrationConfig) -> str:
    table = quote_identifier(config.target_table)
    column = quote_identifier(config.target_column)
    if config.migration_operation == "add_column":
        return f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} boolean"
    index_name = quote_identifier(f"idx_{config.target_table}_{config.target_column}")
    return f"CREATE INDEX IF NOT EXISTS {index_name} ON {table} ({column})"


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    percentile_index = {
        0.50: 49,
        0.95: 94,
        0.99: 98,
    }.get(percentile)
    if percentile_index is None:
        raise ValueError(f"Unsupported percentile: {percentile}")
    return quantiles(values, n=100, method="inclusive")[percentile_index]


def _health_score(stats: _MigrationStats, migration_duration_ms: float, config: MigrationConfig) -> int:
    error_penalty = min(50, stats.errors * 5)
    lock_penalty = min(30, stats.lock_timeouts * 10)
    duration_penalty = 0
    if migration_duration_ms > config.lock_timeout_ms:
        duration_penalty = min(20, int((migration_duration_ms / config.lock_timeout_ms) * 5))
    return max(0, 100 - error_penalty - lock_penalty - duration_penalty)
