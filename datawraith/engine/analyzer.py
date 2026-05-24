"""Rule-based report analysis helpers for Phase 2."""

from __future__ import annotations

from dataclasses import dataclass

from datawraith.core.types import Culprit


@dataclass(frozen=True)
class SlowQuerySample:
    """One observed query sample used by the lightweight analyzer."""

    label: str
    query_text: str
    duration_ms: float


def summarize_slow_queries(samples: list[SlowQuerySample], *, limit: int = 5) -> list[Culprit]:
    """Aggregate slow query samples into ScenarioResult culprits.

    The analyzer intentionally stays rule-based in Phase 2. It does not run
    EXPLAIN against user SQL yet, so the execution plan field contains safe,
    deterministic hints based on the observed query shape.
    """
    if limit < 1:
        return []
    if not samples:
        return []

    grouped: dict[str, list[SlowQuerySample]] = {}
    for sample in samples:
        grouped.setdefault(sample.label, []).append(sample)

    totals = {
        label: sum(sample.duration_ms for sample in label_samples)
        for label, label_samples in grouped.items()
    }
    total_duration = max(sum(totals.values()), 0.001)
    ranked_labels = sorted(totals, key=lambda label: totals[label], reverse=True)

    culprits: list[Culprit] = []
    for rank, label in enumerate(ranked_labels[:limit], start=1):
        label_samples = grouped[label]
        representative = max(label_samples, key=lambda sample: sample.duration_ms)
        mean_exec_time_ms = totals[label] / len(label_samples)
        culprits.append(
            Culprit(
                rank=rank,
                query_text=representative.query_text,
                impact_pct=(totals[label] / total_duration) * 100,
                calls=len(label_samples),
                mean_exec_time_ms=mean_exec_time_ms,
                execution_plan=_hint_for_query(representative.query_text),
            )
        )

    return culprits


def _hint_for_query(query_text: str) -> str:
    """Return a conservative missing-index/full-scan hint for a query shape."""
    normalized = " ".join(query_text.lower().split())
    hints: list[str] = []
    if " join " in normalized and "dw_orders" in normalized and "product_id" in normalized:
        hints.append("Consider an index on dw_orders(product_id) for join-heavy reads.")
    if "where" in normalized and "created_at" in normalized:
        hints.append("Consider an index on created_at if time-window filters become slow.")
    if "group by" in normalized:
        hints.append("GROUP BY workload may full-scan without selective predicates.")
    if "update" in normalized and "where id" in normalized:
        hints.append("UPDATE path expects a primary-key or unique index on id.")
    if not hints:
        hints.append("No safe rule-based hint detected; inspect with EXPLAIN in a real DB session.")
    return " ".join(hints)
