from __future__ import annotations

from datetime import datetime

from datawraith.core.types import HealthMetrics, ScenarioResult, ScenarioType
from datawraith.engine.migration_analysis import (
    MigrationObservation,
    culprits_for_migration,
    migration_suggestions_for_result,
)


def test_culprits_for_migration_reports_lock_pressure() -> None:
    culprits = culprits_for_migration(
        MigrationObservation(
            operation="ALTER TABLE items ADD COLUMN flag boolean",
            lock_timeout_ms=500,
            migration_duration_ms=1200.0,
            blocked_operations=2,
            error_count=2,
        )
    )

    assert len(culprits) == 2
    assert "blocked" in culprits[0].execution_plan


def test_migration_suggestions_include_add_column_advice() -> None:
    result = ScenarioResult(
        scenario_name="migration",
        scenario_type=ScenarioType.MIGRATION,
        config={"migration_operation": "add_column", "lock_timeout_ms": 500},
        started_at=datetime(2026, 5, 24, 12, 0, 0),
        completed_at=datetime(2026, 5, 24, 12, 0, 1),
        duration_seconds=1.0,
        health_score=90,
        metrics=HealthMetrics(
            qps_max=2.0,
            qps_avg=2.0,
            latency_p50_ms=1.0,
            latency_p95_ms=2.0,
            latency_p99_ms=3.0,
            error_count=0,
            error_rate=0.0,
        ),
    )

    suggestions = migration_suggestions_for_result(result)

    assert suggestions[0].provider == "rules"
    assert suggestions[0].risk_level == "low"
    assert "nullable columns" in suggestions[0].reasoning
