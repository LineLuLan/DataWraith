"""Shared Pydantic models and enums for DataWraith."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ScenarioType(StrEnum):
    """Supported scenario identifiers."""

    CONCURRENCY = "concurrency"
    RW_HEAVY = "rw_heavy"
    MIGRATION = "migration"
    SECURITY = "security"


class EventType(StrEnum):
    """Types of events streamed from scenario execution."""

    STARTED = "started"
    LOG = "log"
    METRIC = "metric"
    WARNING = "warning"
    ERROR = "error"
    COMPLETED = "completed"


class Distribution(StrEnum):
    """Synthetic data distribution strategies."""

    UNIFORM = "uniform"
    ZIPFIAN = "zipfian"
    REALISTIC = "realistic"


class ScenarioConfig(BaseModel):
    """Base config for any scenario."""

    model_config = ConfigDict(frozen=True)

    duration_seconds: int = Field(default=60, ge=10, le=3600)
    workers: int = Field(default=100, ge=1, le=10000)
    target_qps: int | None = Field(default=None, ge=1)


class ConcurrencyConfig(ScenarioConfig):
    """Phase 1 concurrency scenario config."""

    concurrent_updates: int = Field(default=1000, ge=10, le=100000)
    target_table: str = Field(min_length=1)
    target_column: str = Field(min_length=1)
    isolation_level: Literal["read_committed", "repeatable_read", "serializable"] = (
        "read_committed"
    )


class RWHeavyConfig(ScenarioConfig):
    """Phase 2 read/write-heavy scenario config."""

    read_write_ratio: float = Field(default=0.7, ge=0.0, le=1.0)
    row_count: int = Field(default=100, ge=10, le=1_000_000)
    operation_limit: int = Field(default=1000, ge=1, le=10_000_000)
    slow_query_threshold_ms: float = Field(default=100.0, ge=1.0)
    products_table: str = Field(default="dw_products", min_length=1)
    customers_table: str = Field(default="dw_customers", min_length=1)
    orders_table: str = Field(default="dw_orders", min_length=1)
    use_window_functions: bool = True
    use_multi_join: bool = True


class MigrationConfig(ScenarioConfig):
    """Phase 3 migration-lock scenario config."""

    target_table: str = Field(default="dw_migration_items", min_length=1)
    target_column: str = Field(default="phase3_flag", min_length=1)
    migration_operation: Literal["add_column", "create_index"] = "add_column"
    row_count: int = Field(default=100, ge=10, le=1_000_000)
    operation_limit: int = Field(default=500, ge=1, le=10_000_000)
    lock_timeout_ms: int = Field(default=500, ge=50, le=60_000)
    statement_timeout_ms: int = Field(default=5_000, ge=100, le=300_000)
    hold_lock_ms: int = Field(default=0, ge=0, le=60_000)


class ScenarioEvent(BaseModel):
    """Event streamed from a scenario to the TUI or CLI."""

    type: EventType
    timestamp: datetime = Field(default_factory=datetime.now)
    message: str | None = None
    data: dict[str, Any] | None = None


class HealthMetrics(BaseModel):
    """Aggregated health metrics for a scenario run."""

    qps_max: float
    qps_avg: float
    latency_p50_ms: float
    latency_p95_ms: float
    latency_p99_ms: float
    error_count: int
    error_rate: float
    deadlock_count: int = 0
    lock_wait_ms_total: float = 0.0
    connection_saturation_pct: float = 0.0


class Culprit(BaseModel):
    """A query or table that caused measurable performance impact."""

    rank: int
    query_text: str
    impact_pct: float
    calls: int
    mean_exec_time_ms: float
    execution_plan: str


class ScenarioResult(BaseModel):
    """Final output of a scenario run."""

    scenario_name: str
    scenario_type: ScenarioType
    config: dict[str, Any]
    started_at: datetime
    completed_at: datetime
    duration_seconds: float
    health_score: int = Field(ge=0, le=100)
    metrics: HealthMetrics
    top_culprits: list[Culprit] = Field(default_factory=list)
    raw_logs: list[str] = Field(default_factory=list)


class AISuggestion(BaseModel):
    """AI-generated suggestion contract for Phase 3+."""

    provider: str
    model: str
    reasoning: str
    sql_fix: str | None = None
    risk_level: Literal["low", "medium", "high"]
    rollback_plan: str | None = None
    tokens_used: int | None = None
    cost_usd: float | None = None


class SeedResult(BaseModel):
    """Result of inserting generated seed data into ShadowDB."""

    table: str
    rows_requested: int
    rows_inserted: int
    duration_seconds: float = Field(ge=0)
