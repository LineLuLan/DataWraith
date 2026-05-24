from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from datawraith.core.types import HealthMetrics, ScenarioResult, ScenarioType
from datawraith.output.ascii_renderer import render_result
from datawraith.output.json_exporter import JSONExporter


def _result() -> ScenarioResult:
    return ScenarioResult(
        scenario_name="concurrency",
        scenario_type=ScenarioType.CONCURRENCY,
        config={"workers": 10},
        started_at=datetime(2026, 5, 24, 12, 0, 0),
        completed_at=datetime(2026, 5, 24, 12, 0, 1),
        duration_seconds=1.0,
        health_score=95,
        metrics=HealthMetrics(
            qps_max=0.0,
            qps_avg=0.0,
            latency_p50_ms=0.0,
            latency_p95_ms=0.0,
            latency_p99_ms=0.0,
            error_count=0,
            error_rate=0.0,
        ),
    )


def test_json_exporter_writes_result(tmp_path: Path) -> None:
    output_path = tmp_path / "report.json"

    JSONExporter().export(_result(), output_path)

    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert data["scenario_name"] == "concurrency"
    assert data["scenario_type"] == "concurrency"


def test_ascii_renderer_includes_summary() -> None:
    rendered = render_result(_result())

    assert "CONCURRENCY" in rendered
    assert "Health Score: 95/100" in rendered
