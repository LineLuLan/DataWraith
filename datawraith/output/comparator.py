"""Compare DataWraith JSON scenario reports."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from datawraith.core.exceptions import DataWraithError
from datawraith.core.types import ScenarioResult


class MetricDelta(BaseModel):
    """One comparable metric delta between two reports."""

    name: str
    baseline: float
    current: float
    delta: float
    delta_pct: float


class ReportComparison(BaseModel):
    """Summary of two report files."""

    baseline_scenario: str
    current_scenario: str
    deltas: list[MetricDelta]


def load_result(path: Path) -> ScenarioResult:
    """Load and validate a ScenarioResult JSON report."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return ScenarioResult.model_validate(payload)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise DataWraithError(f"Could not load report {path}: {exc}") from exc


def compare_results(baseline: ScenarioResult, current: ScenarioResult) -> ReportComparison:
    """Compare two ScenarioResult values using stable top-level metrics."""
    metric_pairs = {
        "health_score": (float(baseline.health_score), float(current.health_score)),
        "qps_avg": (baseline.metrics.qps_avg, current.metrics.qps_avg),
        "qps_max": (baseline.metrics.qps_max, current.metrics.qps_max),
        "latency_p95_ms": (baseline.metrics.latency_p95_ms, current.metrics.latency_p95_ms),
        "latency_p99_ms": (baseline.metrics.latency_p99_ms, current.metrics.latency_p99_ms),
        "error_rate": (baseline.metrics.error_rate, current.metrics.error_rate),
    }
    deltas = [
        MetricDelta(
            name=name,
            baseline=baseline_value,
            current=current_value,
            delta=current_value - baseline_value,
            delta_pct=_delta_pct(baseline_value, current_value),
        )
        for name, (baseline_value, current_value) in metric_pairs.items()
    ]
    return ReportComparison(
        baseline_scenario=baseline.scenario_name,
        current_scenario=current.scenario_name,
        deltas=deltas,
    )


def render_comparison(comparison: ReportComparison) -> str:
    """Render a compact terminal comparison table."""
    lines = [
        f"Comparing {comparison.baseline_scenario} -> {comparison.current_scenario}",
        "Metric             Baseline      Current       Delta      Delta %",
    ]
    for delta in comparison.deltas:
        lines.append(
            f"{delta.name:<18} "
            f"{delta.baseline:>9.2f} "
            f"{delta.current:>12.2f} "
            f"{delta.delta:>11.2f} "
            f"{delta.delta_pct:>10.1f}%"
        )
    return "\n".join(lines)


def _delta_pct(baseline: float, current: float) -> float:
    if baseline == 0:
        return 0.0 if current == 0 else 100.0
    return ((current - baseline) / abs(baseline)) * 100
