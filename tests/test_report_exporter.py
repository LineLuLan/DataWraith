from __future__ import annotations

import json
from datetime import datetime

from datawraith.core.types import Culprit, HealthMetrics, ScenarioResult, ScenarioType
from datawraith.output.report_exporter import export_report


def _security_result() -> ScenarioResult:
    return ScenarioResult(
        scenario_name="security",
        scenario_type=ScenarioType.SECURITY,
        config={},
        started_at=datetime(2026, 5, 24, 12, 0, 0),
        completed_at=datetime(2026, 5, 24, 12, 0, 1),
        duration_seconds=1.0,
        health_score=80,
        metrics=HealthMetrics(
            qps_max=1.0,
            qps_avg=1.0,
            latency_p50_ms=0.0,
            latency_p95_ms=0.0,
            latency_p99_ms=0.0,
            error_count=1,
            error_rate=1.0,
        ),
        top_culprits=[
            Culprit(
                rank=1,
                query_text="SELECT relrowsecurity FROM pg_class",
                impact_pct=90.0,
                calls=1,
                mean_exec_time_ms=0.0,
                execution_plan="DW-SEC-001: RLS disabled",
            )
        ],
    )


def test_export_report_writes_sarif(tmp_path) -> None:  # type: ignore[no-untyped-def]
    output = tmp_path / "security.sarif"

    export_report(_security_result(), output, "sarif")

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["version"] == "2.1.0"
    assert payload["runs"][0]["results"][0]["level"] == "error"


def test_export_report_writes_junit(tmp_path) -> None:  # type: ignore[no-untyped-def]
    output = tmp_path / "security.xml"

    export_report(_security_result(), output, "junit")

    text = output.read_text(encoding="utf-8")
    assert "<testsuite" in text
    assert "<failure" in text


def test_export_report_writes_minimal_pdf(tmp_path) -> None:  # type: ignore[no-untyped-def]
    output = tmp_path / "security.pdf"

    export_report(_security_result(), output, "pdf")

    assert output.read_bytes().startswith(b"%PDF-1.4")
