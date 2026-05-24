from __future__ import annotations

from datawraith.engine.security_analysis import (
    SecurityFinding,
    findings_to_culprits,
    security_health_score,
)


def test_security_findings_to_culprits_only_includes_failures() -> None:
    culprits = findings_to_culprits(
        [
            SecurityFinding(
                rule_id="DW-SEC-001",
                title="RLS enabled",
                severity="high",
                message="ok",
                query_text="SELECT 1",
                passed=True,
            ),
            SecurityFinding(
                rule_id="DW-SEC-002",
                title="Tenant isolation",
                severity="high",
                message="leak",
                query_text="SELECT *",
                passed=False,
            ),
        ]
    )

    assert len(culprits) == 1
    assert culprits[0].impact_pct == 90.0
    assert "DW-SEC-002" in culprits[0].execution_plan


def test_security_health_score_penalizes_failed_findings() -> None:
    score = security_health_score(
        [
            SecurityFinding(
                rule_id="DW-SEC-002",
                title="Tenant isolation",
                severity="high",
                message="leak",
                query_text="SELECT *",
                passed=False,
            )
        ],
        errors=1,
    )

    assert score == 55
