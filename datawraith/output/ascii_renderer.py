"""ASCII rendering for terminal summaries."""

from __future__ import annotations

from datawraith.core.types import ScenarioResult


def render_result(result: ScenarioResult) -> str:
    """Render a scenario result as plain terminal text."""
    lines = [
        f"=== {result.scenario_name.upper()} ===",
        f"Duration: {result.duration_seconds:.1f}s",
        f"Health Score: {result.health_score}/100",
        "",
        "Metrics:",
        f"  QPS avg/max: {result.metrics.qps_avg:.0f} / {result.metrics.qps_max:.0f}",
        f"  Latency p99: {result.metrics.latency_p99_ms:.1f}ms",
        f"  Errors:      {result.metrics.error_count}",
        f"  Deadlocks:   {result.metrics.deadlock_count}",
        "",
        "Top Culprits:",
    ]
    if not result.top_culprits:
        lines.append("  None recorded")
    for culprit in result.top_culprits[:3]:
        lines.append(f"  {culprit.rank}. {culprit.query_text[:60]} ({culprit.impact_pct:.1f}%)")
    return "\n".join(lines)
