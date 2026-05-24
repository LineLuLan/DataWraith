"""Phase 2 read/write-heavy PostgreSQL workload scenario."""

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
    RWHeavyConfig,
    ScenarioEvent,
    ScenarioResult,
    ScenarioType,
)
from datawraith.engine.analyzer import SlowQuerySample, summarize_slow_queries
from datawraith.engine.scenarios.base import Scenario
from datawraith.engine.seeder import quote_identifier


class RWHeavyScenario(Scenario):
    """Mixed read/insert/update workload with self-contained seed data."""

    name = "rw-heavy"
    display_name = "Read/Write Heavy"

    def __init__(self, db: ShadowDB | None, config: RWHeavyConfig) -> None:
        super().__init__(db, config)
        self.config: RWHeavyConfig = config

    def validate_config(self) -> list[str]:
        errors: list[str] = []
        if self.db is None:
            errors.append("ShadowDB is required to run rw-heavy scenario")
        if self.config.workers < 1:
            errors.append("workers must be >= 1")
        for table_name in (
            self.config.products_table,
            self.config.customers_table,
            self.config.orders_table,
        ):
            if "\x00" in table_name:
                errors.append("table names cannot contain NUL bytes")
        return errors

    async def run(self) -> AsyncIterator[ScenarioEvent]:
        started_at = datetime.now()
        started_perf = perf_counter()
        yield ScenarioEvent(
            type=EventType.STARTED,
            message=f"Starting rw-heavy workload with {self.config.workers} workers",
        )

        stats = _RWHeavyStats()
        logs: list[str] = []
        event_queue: asyncio.Queue[ScenarioEvent] = asyncio.Queue()
        worker_tasks: list[asyncio.Task[None]] = []
        reporter_task: asyncio.Task[None] | None = None

        try:
            if self.db is None:
                raise RuntimeError("ShadowDB is required to run rw-heavy scenario")
            uri = self.db.get_uri()
            await _prepare_schema_and_seed(uri, self.config)
            yield ScenarioEvent(
                type=EventType.LOG,
                message=(
                    "Prepared rw-heavy seed data: "
                    f"{self.config.row_count} products/customers plus baseline orders"
                ),
            )

            deadline = perf_counter() + self.config.duration_seconds
            for worker_id in range(self.config.workers):
                worker_tasks.append(
                    asyncio.create_task(
                        _worker(
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
            message = f"RW-heavy scenario failed: {exc}"
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
        metrics = HealthMetrics(
            qps_max=stats.qps_max,
            qps_avg=stats.completed / duration_seconds,
            latency_p50_ms=_percentile(stats.latencies_ms, 0.50),
            latency_p95_ms=_percentile(stats.latencies_ms, 0.95),
            latency_p99_ms=_percentile(stats.latencies_ms, 0.99),
            error_count=stats.errors,
            error_rate=stats.errors / max(stats.completed + stats.errors, 1),
        )
        result = ScenarioResult(
            scenario_name=self.name,
            scenario_type=ScenarioType.RW_HEAVY,
            config=self.config.model_dump(mode="json"),
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=duration_seconds,
            health_score=_health_score(stats, metrics.latency_p99_ms, self.config),
            metrics=metrics,
            top_culprits=summarize_slow_queries(stats.slow_samples),
            raw_logs=logs[-100:],
        )
        yield ScenarioEvent(
            type=EventType.COMPLETED,
            message="RW-heavy scenario completed.",
            data={"result": result.model_dump(mode="json")},
        )


class _RWHeavyStats:
    """Mutable runtime stats shared by rw-heavy workers."""

    def __init__(self) -> None:
        self.completed = 0
        self.reads = 0
        self.writes = 0
        self.errors = 0
        self.latencies_ms: list[float] = []
        self.slow_samples: list[SlowQuerySample] = []
        self.qps_max = 0.0


async def _prepare_schema_and_seed(uri: str, config: RWHeavyConfig) -> None:
    customers = quote_identifier(config.customers_table)
    products = quote_identifier(config.products_table)
    orders = quote_identifier(config.orders_table)
    conn = await asyncpg.connect(uri)
    try:
        await conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {customers} (
                id integer PRIMARY KEY,
                email text NOT NULL UNIQUE,
                name text NOT NULL,
                created_at timestamptz NOT NULL DEFAULT now()
            )
            """
        )
        await conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {products} (
                id integer PRIMARY KEY,
                name text NOT NULL,
                category text NOT NULL,
                stock integer NOT NULL,
                price numeric(12, 2) NOT NULL,
                updated_at timestamptz NOT NULL DEFAULT now()
            )
            """
        )
        await conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {orders} (
                id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                customer_id integer NOT NULL REFERENCES {customers}(id),
                product_id integer NOT NULL REFERENCES {products}(id),
                quantity integer NOT NULL,
                status text NOT NULL,
                created_at timestamptz NOT NULL DEFAULT now()
            )
            """
        )
        await conn.execute(
            f"""
            INSERT INTO {customers} (id, email, name, created_at)
            SELECT id,
                   'customer-' || id || '@example.test',
                   'Customer ' || id,
                   now() - ((id % 30) || ' days')::interval
            FROM generate_series(1, $1) AS id
            ON CONFLICT (id) DO NOTHING
            """,
            config.row_count,
        )
        await conn.execute(
            f"""
            INSERT INTO {products} (id, name, category, stock, price, updated_at)
            SELECT id,
                   'Product ' || id,
                   'category-' || (id % 10),
                   100 + (id % 50),
                   ((id % 100) + 1)::numeric,
                   now()
            FROM generate_series(1, $1) AS id
            ON CONFLICT (id) DO NOTHING
            """,
            config.row_count,
        )
        await conn.execute(
            f"""
            INSERT INTO {orders} (customer_id, product_id, quantity, status, created_at)
            SELECT ((id - 1) % $1) + 1,
                   ((id - 1) % $1) + 1,
                   (id % 5) + 1,
                   'seeded',
                   now() - ((id % 14) || ' days')::interval
            FROM generate_series(1, $2) AS id
            """,
            config.row_count,
            max(config.row_count, 20),
        )
    finally:
        await conn.close()


async def _worker(
    *,
    worker_id: int,
    uri: str,
    config: RWHeavyConfig,
    deadline: float,
    stats: _RWHeavyStats,
    logs: list[str],
) -> None:
    conn = await asyncpg.connect(uri)
    try:
        operation = worker_id
        while perf_counter() < deadline and stats.completed < config.operation_limit:
            label, query, args = _operation_for(operation, config)
            started = perf_counter()
            try:
                if label == "read":
                    await conn.fetch(query, *args)
                    stats.reads += 1
                else:
                    await conn.execute(query, *args)
                    stats.writes += 1
                duration_ms = (perf_counter() - started) * 1000
                stats.completed += 1
                stats.latencies_ms.append(duration_ms)
                if duration_ms >= config.slow_query_threshold_ms:
                    stats.slow_samples.append(
                        SlowQuerySample(label=label, query_text=query, duration_ms=duration_ms)
                    )
            except asyncpg.PostgresError as exc:
                stats.errors += 1
                logs.append(f"worker={worker_id} {label} error: {exc}")
            operation += config.workers
    finally:
        await conn.close()


def _operation_for(operation: int, config: RWHeavyConfig) -> tuple[str, str, tuple[int, ...]]:
    read_cutoff = int(config.read_write_ratio * 100)
    product_id = (operation % config.row_count) + 1
    customer_id = ((operation * 3) % config.row_count) + 1
    if operation % 100 < read_cutoff:
        return (
            "read",
            _read_query(config),
            (max(1, product_id - 20), min(config.row_count, product_id + 20)),
        )
    if operation % 2 == 0:
        return (
            "update",
            (
                f"UPDATE {quote_identifier(config.products_table)} "
                "SET stock = GREATEST(stock - 1, 0), updated_at = now() "
                "WHERE id = $1"
            ),
            (product_id,),
        )
    return (
        "insert",
        (
            f"INSERT INTO {quote_identifier(config.orders_table)} "
            "(customer_id, product_id, quantity, status, created_at) "
            "VALUES ($1, $2, $3, 'open', now())"
        ),
        (customer_id, product_id, (operation % 5) + 1),
    )


def _read_query(config: RWHeavyConfig) -> str:
    products = quote_identifier(config.products_table)
    orders = quote_identifier(config.orders_table)
    if config.use_multi_join:
        return (
            "SELECT p.category, count(o.id) AS order_count, "
            "avg(p.price) AS avg_price, coalesce(sum(o.quantity), 0) AS total_quantity "
            f"FROM {products} p "
            f"LEFT JOIN {orders} o ON o.product_id = p.id "
            "WHERE p.id BETWEEN $1 AND $2 "
            "GROUP BY p.category "
            "ORDER BY total_quantity DESC "
            "LIMIT 10"
        )
    if config.use_window_functions:
        return (
            "SELECT id, category, price, "
            "avg(price) OVER (PARTITION BY category) AS category_avg "
            f"FROM {products} "
            "WHERE id BETWEEN $1 AND $2 "
            "ORDER BY id"
        )
    return f"SELECT id, name, stock, price FROM {products} WHERE id BETWEEN $1 AND $2"


async def _report_metrics(
    queue: asyncio.Queue[ScenarioEvent],
    stats: _RWHeavyStats,
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
                message="RW-heavy metrics update",
                data={
                    "completed": stats.completed,
                    "reads": stats.reads,
                    "writes": stats.writes,
                    "errors": stats.errors,
                    "qps": qps,
                },
            )
        )


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


def _health_score(stats: _RWHeavyStats, p99_latency_ms: float, config: RWHeavyConfig) -> int:
    error_penalty = min(60, stats.errors * 5)
    latency_penalty = 0
    if p99_latency_ms > config.slow_query_threshold_ms:
        latency_penalty = min(30, int((p99_latency_ms / config.slow_query_threshold_ms) * 5))
    slow_query_penalty = min(20, len(stats.slow_samples))
    return max(0, 100 - error_penalty - latency_penalty - slow_query_penalty)
