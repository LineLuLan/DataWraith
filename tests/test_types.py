from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

from datawraith.core.types import (
    ConcurrencyConfig,
    HealthMetrics,
    ScenarioResult,
    ScenarioType,
)


def test_concurrency_config_is_frozen() -> None:
    config = ConcurrencyConfig(target_table="products", target_column="stock")

    with pytest.raises(ValidationError):
        config.workers = 20


def test_scenario_result_model_dump_json() -> None:
    result = ScenarioResult(
        scenario_name="concurrency",
        scenario_type=ScenarioType.CONCURRENCY,
        config={"workers": 10},
        started_at=datetime(2026, 5, 24, 12, 0, 0),
        completed_at=datetime(2026, 5, 24, 12, 0, 1),
        duration_seconds=1.0,
        health_score=90,
        metrics=HealthMetrics(
            qps_max=10.0,
            qps_avg=8.0,
            latency_p50_ms=1.0,
            latency_p95_ms=2.0,
            latency_p99_ms=3.0,
            error_count=0,
            error_rate=0.0,
        ),
    )

    dumped = result.model_dump(mode="json")

    assert dumped["scenario_type"] == "concurrency"
    assert dumped["started_at"] == "2026-05-24T12:00:00"
