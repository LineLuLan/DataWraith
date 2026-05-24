"""Phase 1 Concurrency Test scenario."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from datetime import datetime
from statistics import quantiles
from time import perf_counter

import asyncpg

from datawraith.core.shadow_db import ShadowDB
from datawraith.core.types import (
    ConcurrencyConfig,
    EventType,
    HealthMetrics,
    ScenarioEvent,
    ScenarioResult,
    ScenarioType,
)
from datawraith.engine.scenarios.base import Scenario
from datawraith.engine.seeder import quote_identifier


class ConcurrencyScenario(Scenario):
    """MVP concurrent UPDATE workload for Phase 1."""

    name = "concurrency"
    display_name = "Concurrency Test"

    def __init__(self, db: ShadowDB | None, config: ConcurrencyConfig) -> None:
        super().__init__(db, config)
        self.config: ConcurrencyConfig = config

    def validate_config(self) -> list[str]:
        errors: list[str] = []
        if self.config.workers < 2:
            errors.append("Need at least 2 workers for concurrency test")
        if not self.config.target_table:
            errors.append("target_table is required")
        if not self.config.target_column:
            errors.append("target_column is required")
        if self.db is None:
            errors.append("ShadowDB is required to run concurrency test")
        return errors

    async def run(self) -> AsyncIterator[ScenarioEvent]:
        started_at = datetime.now()
        started_perf = perf_counter()
        yield ScenarioEvent(
            type=EventType.STARTED,
            message=(
                f"Starting {self.config.workers} workers on "
                f"{self.config.target_table}.{self.config.target_column}"
            ),
        )

        stats = _ConcurrencyStats()
        logs: list[str] = []
        event_queue: asyncio.Queue[ScenarioEvent] = asyncio.Queue()
        worker_tasks: list[asyncio.Task[None]] = []
        reporter_task: asyncio.Task[None] | None = None

        try:
            if self.db is None:
                raise RuntimeError("ShadowDB is required to run concurrency test")
            uri = self.db.get_uri()
            row_count = await _get_row_count(uri, self.config.target_table)
            if row_count < 1:
                raise RuntimeError(f"Target table {self.config.target_table} has no rows to update")

            query = _build_update_query(self.config.target_table, self.config.target_column)
            deadline = perf_counter() + self.config.duration_seconds
            for worker_id in range(self.config.workers):
                worker_tasks.append(
                    asyncio.create_task(
                        _worker(
                            worker_id=worker_id,
                            uri=uri,
                            query=query,
                            row_count=row_count,
                            deadline=deadline,
                            max_operations=self.config.concurrent_updates,
                            stats=stats,
                            logs=logs,
                        )
                    )
                )
            reporter_task = asyncio.create_task(
                _report_metrics(event_queue, stats, started_perf, deadline)
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
            message = f"Concurrency scenario failed: {exc}"
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
        result = ScenarioResult(
            scenario_name=self.name,
            scenario_type=ScenarioType.CONCURRENCY,
            config=self.config.model_dump(mode="json"),
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=duration_seconds,
            health_score=_health_score(stats),
            metrics=HealthMetrics(
                qps_max=stats.qps_max,
                qps_avg=stats.completed / duration_seconds,
                latency_p50_ms=_percentile(stats.latencies_ms, 0.50),
                latency_p95_ms=_percentile(stats.latencies_ms, 0.95),
                latency_p99_ms=_percentile(stats.latencies_ms, 0.99),
                error_count=stats.errors,
                error_rate=stats.errors / max(stats.completed + stats.errors, 1),
                deadlock_count=stats.deadlocks,
            ),
            raw_logs=logs[-100:],
        )
        yield ScenarioEvent(
            type=EventType.COMPLETED,
            message="Concurrency scenario completed.",
            data={"result": result.model_dump(mode="json")},
        )


class _ConcurrencyStats:
    """Mutable stats shared by scenario tasks."""

    def __init__(self) -> None:
        self.completed = 0
        self.errors = 0
        self.deadlocks = 0
        self.latencies_ms: list[float] = []
        self.qps_max = 0.0


async def _get_row_count(uri: str, table: str) -> int:
    conn = await asyncpg.connect(uri)
    try:
        value = await conn.fetchval(f"SELECT count(*) FROM {quote_identifier(table)}")
        return int(value or 0)
    finally:
        await conn.close()


async def _worker(
    *,
    worker_id: int,
    uri: str,
    query: str,
    row_count: int,
    deadline: float,
    max_operations: int,
    stats: _ConcurrencyStats,
    logs: list[str],
) -> None:
    conn = await asyncpg.connect(uri)
    try:
        operation = worker_id
        while perf_counter() < deadline and stats.completed < max_operations:
            row_id = (operation % row_count) + 1
            started = perf_counter()
            try:
                await conn.execute(query, row_id)
                stats.completed += 1
                stats.latencies_ms.append((perf_counter() - started) * 1000)
            except asyncpg.exceptions.DeadlockDetectedError as exc:
                stats.deadlocks += 1
                stats.errors += 1
                logs.append(f"worker={worker_id} deadlock: {exc}")
            except asyncpg.PostgresError as exc:
                stats.errors += 1
                logs.append(f"worker={worker_id} postgres error: {exc}")
            operation += 1
    finally:
        await conn.close()


async def _report_metrics(
    queue: asyncio.Queue[ScenarioEvent],
    stats: _ConcurrencyStats,
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
                message="Concurrency metrics update",
                data={
                    "completed": stats.completed,
                    "errors": stats.errors,
                    "deadlocks": stats.deadlocks,
                    "qps": qps,
                },
            )
        )


def _build_update_query(table: str, column: str) -> str:
    return (
        f"UPDATE {quote_identifier(table)} "
        f"SET {quote_identifier(column)} = {quote_identifier(column)} - 1 "
        "WHERE id = $1"
    )


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    if percentile == 0.50:
        return quantiles(values, n=100, method="inclusive")[49]
    if percentile == 0.95:
        return quantiles(values, n=100, method="inclusive")[94]
    if percentile == 0.99:
        return quantiles(values, n=100, method="inclusive")[98]
    raise ValueError(f"Unsupported percentile: {percentile}")


def _health_score(stats: _ConcurrencyStats) -> int:
    penalty = min(80, stats.errors * 5 + stats.deadlocks * 10)
    return max(0, 100 - penalty)
