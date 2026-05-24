"""Rule-based security and isolation analysis for Phase 4."""

from __future__ import annotations

from dataclasses import dataclass

from datawraith.core.types import Culprit


@dataclass(frozen=True)
class SecurityFinding:
    """One local security finding from a ShadowDB-only check."""

    rule_id: str
    title: str
    severity: str
    message: str
    query_text: str
    passed: bool


SQL_INJECTION_PAYLOADS: tuple[str, ...] = (
    "' OR '1'='1",
    "'; DROP TABLE users; --",
    "admin' --",
    "1 OR 1=1",
    "' UNION SELECT NULL --",
    "\" OR \"1\"=\"1",
    "'; SELECT pg_sleep(1); --",
    "%' OR '%'='%",
)


def findings_to_culprits(findings: list[SecurityFinding]) -> list[Culprit]:
    """Convert failed findings to ScenarioResult culprits."""
    failed = [finding for finding in findings if not finding.passed]
    culprits: list[Culprit] = []
    for rank, finding in enumerate(failed, start=1):
        culprits.append(
            Culprit(
                rank=rank,
                query_text=finding.query_text,
                impact_pct=_severity_impact(finding.severity),
                calls=1,
                mean_exec_time_ms=0.0,
                execution_plan=f"{finding.rule_id}: {finding.title}. {finding.message}",
            )
        )
    return culprits


def security_health_score(findings: list[SecurityFinding], errors: int) -> int:
    """Calculate a conservative security score from local findings."""
    penalty = min(40, errors * 10)
    for finding in findings:
        if finding.passed:
            continue
        if finding.severity == "high":
            penalty += 35
        elif finding.severity == "medium":
            penalty += 20
        else:
            penalty += 10
    return max(0, 100 - min(100, penalty))


def _severity_impact(severity: str) -> float:
    if severity == "high":
        return 90.0
    if severity == "medium":
        return 60.0
    return 30.0
