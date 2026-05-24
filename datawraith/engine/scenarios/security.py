"""Phase 4 security and tenant-isolation scenario."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime
from time import perf_counter
from typing import Any

import asyncpg

from datawraith.core.shadow_db import ShadowDB
from datawraith.core.types import (
    EventType,
    HealthMetrics,
    ScenarioEvent,
    ScenarioResult,
    ScenarioType,
    SecurityConfig,
)
from datawraith.engine.scenarios.base import Scenario
from datawraith.engine.security_analysis import (
    SQL_INJECTION_PAYLOADS,
    SecurityFinding,
    findings_to_culprits,
    security_health_score,
)
from datawraith.engine.seeder import quote_identifier


class SecurityScenario(Scenario):
    """Local RLS, tenant isolation, fuzz, and privilege checks."""

    name = "security"
    display_name = "Security & Isolation"

    def __init__(self, db: ShadowDB | None, config: SecurityConfig) -> None:
        super().__init__(db, config)
        self.config: SecurityConfig = config

    def validate_config(self) -> list[str]:
        errors: list[str] = []
        if self.db is None:
            errors.append("ShadowDB is required to run security scenario")
        for identifier in (
            self.config.records_table,
            self.config.tenants_table,
            self.config.users_table,
        ):
            if "\x00" in identifier:
                errors.append("Security identifiers cannot contain NUL bytes")
        return errors

    async def run(self) -> AsyncIterator[ScenarioEvent]:
        started_at = datetime.now()
        started_perf = perf_counter()
        findings: list[SecurityFinding] = []
        logs: list[str] = []
        errors = 0

        yield ScenarioEvent(
            type=EventType.STARTED,
            message="Starting local security and tenant-isolation checks",
        )

        try:
            if self.db is None:
                raise RuntimeError("ShadowDB is required to run security scenario")
            uri = self.db.get_uri()
            await _prepare_security_schema(uri, self.config)
            yield ScenarioEvent(
                type=EventType.LOG,
                message=(
                    "Prepared security fixtures: "
                    f"{self.config.tenants} tenants x {self.config.rows_per_tenant} records"
                ),
            )

            findings.extend(await _check_rls_isolation(uri, self.config))
            findings.extend(await _run_sql_injection_fuzz(uri, self.config))
            if self.config.check_privileges:
                findings.extend(await _check_privilege_posture(uri, self.config))
        except (asyncpg.PostgresError, OSError, RuntimeError) as exc:
            errors += 1
            message = f"Security scenario failed: {exc}"
            logs.append(message)
            findings.append(
                SecurityFinding(
                    rule_id="DW-SEC-000",
                    title="Security scenario execution failed",
                    severity="high",
                    message=str(exc),
                    query_text="security scenario",
                    passed=False,
                )
            )
            yield ScenarioEvent(type=EventType.ERROR, message=message)

        completed_at = datetime.now()
        duration_seconds = max((completed_at - started_at).total_seconds(), 0.001)
        checks_completed = len(findings)
        failed_findings = [finding for finding in findings if not finding.passed]
        for finding in findings:
            event_type = EventType.LOG if finding.passed else EventType.WARNING
            yield ScenarioEvent(
                type=event_type,
                message=f"{finding.rule_id} {'PASS' if finding.passed else 'FAIL'}: {finding.title}",
                data={"finding": finding.__dict__},
            )

        result = ScenarioResult(
            scenario_name=self.name,
            scenario_type=ScenarioType.SECURITY,
            config=self.config.model_dump(mode="json"),
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=duration_seconds,
            health_score=security_health_score(findings, errors),
            metrics=HealthMetrics(
                qps_max=checks_completed / max(perf_counter() - started_perf, 0.001),
                qps_avg=checks_completed / duration_seconds,
                latency_p50_ms=0.0,
                latency_p95_ms=0.0,
                latency_p99_ms=0.0,
                error_count=len(failed_findings) + errors,
                error_rate=(len(failed_findings) + errors) / max(checks_completed, 1),
            ),
            top_culprits=findings_to_culprits(findings),
            raw_logs=logs + [_finding_log(finding) for finding in findings],
        )
        yield ScenarioEvent(
            type=EventType.COMPLETED,
            message="Security scenario completed.",
            data={"result": result.model_dump(mode="json")},
        )


async def _prepare_security_schema(uri: str, config: SecurityConfig) -> None:
    tenants = quote_identifier(config.tenants_table)
    users = quote_identifier(config.users_table)
    records = quote_identifier(config.records_table)
    conn = await asyncpg.connect(uri)
    try:
        await conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {tenants} (
                id integer PRIMARY KEY,
                name text NOT NULL
            )
            """
        )
        await conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {users} (
                id integer PRIMARY KEY,
                tenant_id integer NOT NULL REFERENCES {tenants}(id),
                email text NOT NULL UNIQUE
            )
            """
        )
        await conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {records} (
                id integer PRIMARY KEY,
                tenant_id integer NOT NULL REFERENCES {tenants}(id),
                owner_user_id integer NOT NULL REFERENCES {users}(id),
                title text NOT NULL,
                secret_value text NOT NULL
            )
            """
        )
        await conn.execute(
            f"""
            INSERT INTO {tenants} (id, name)
            SELECT id, 'Tenant ' || id
            FROM generate_series(1, $1) AS id
            ON CONFLICT (id) DO NOTHING
            """,
            config.tenants,
        )
        await conn.execute(
            f"""
            INSERT INTO {users} (id, tenant_id, email)
            SELECT id, ((id - 1) % $1) + 1, 'user-' || id || '@example.test'
            FROM generate_series(1, $2) AS id
            ON CONFLICT (id) DO NOTHING
            """,
            config.tenants,
            config.tenants * 2,
        )
        total_records = config.tenants * config.rows_per_tenant
        await conn.execute(
            f"""
            INSERT INTO {records} (id, tenant_id, owner_user_id, title, secret_value)
            SELECT id,
                   ((id - 1) % $1) + 1,
                   (((id - 1) % ($1 * 2)) + 1),
                   'record-' || id,
                   'secret-' || id
            FROM generate_series(1, $2) AS id
            ON CONFLICT (id) DO NOTHING
            """,
            config.tenants,
            total_records,
        )
        if config.enforce_rls:
            await conn.execute(f"ALTER TABLE {records} ENABLE ROW LEVEL SECURITY")
            await conn.execute(f"ALTER TABLE {records} FORCE ROW LEVEL SECURITY")
            await conn.execute(
                f"DROP POLICY IF EXISTS datawraith_tenant_isolation ON {records}"
            )
            await conn.execute(
                f"""
                CREATE POLICY datawraith_tenant_isolation ON {records}
                USING (
                    tenant_id = NULLIF(current_setting('datawraith.tenant_id', true), '')::integer
                )
                """
            )
    finally:
        await conn.close()


async def _check_rls_isolation(uri: str, config: SecurityConfig) -> list[SecurityFinding]:
    records = quote_identifier(config.records_table)
    conn = await asyncpg.connect(uri)
    try:
        rls_enabled = bool(
            await conn.fetchval(
                "SELECT relrowsecurity FROM pg_class WHERE relname = $1",
                config.records_table,
            )
        )
        await conn.execute("SET datawraith.tenant_id = '1'")
        leaked_count = int(
            await conn.fetchval(
                f"SELECT count(*) FROM {records} WHERE tenant_id <> 1",
            )
            or 0
        )
    finally:
        await conn.close()

    return [
        SecurityFinding(
            rule_id="DW-SEC-001",
            title="RLS is enabled on tenant records",
            severity="high",
            message="Tenant records table should enforce row-level security.",
            query_text="SELECT relrowsecurity FROM pg_class",
            passed=rls_enabled,
        ),
        SecurityFinding(
            rule_id="DW-SEC-002",
            title="Tenant-scoped query does not leak other tenants",
            severity="high",
            message=f"Observed {leaked_count} cross-tenant rows while tenant context was 1.",
            query_text=f"SELECT count(*) FROM {records} WHERE tenant_id <> 1",
            passed=leaked_count == 0,
        ),
    ]


async def _run_sql_injection_fuzz(uri: str, config: SecurityConfig) -> list[SecurityFinding]:
    records = quote_identifier(config.records_table)
    conn = await asyncpg.connect(uri)
    unexpected_matches = 0
    payloads = SQL_INJECTION_PAYLOADS[: config.fuzz_payload_limit]
    try:
        await conn.execute("SET datawraith.tenant_id = '1'")
        for payload in payloads:
            rows = await conn.fetch(f"SELECT id FROM {records} WHERE title = $1", payload)
            unexpected_matches += len(_rows_to_list(rows))
    finally:
        await conn.close()

    return [
        SecurityFinding(
            rule_id="DW-SEC-003",
            title="SQL injection fuzz payloads are parameterized",
            severity="high",
            message=f"Observed {unexpected_matches} unexpected rows from fuzz payloads.",
            query_text=f"SELECT id FROM {records} WHERE title = $1",
            passed=unexpected_matches == 0,
        )
    ]


async def _check_privilege_posture(uri: str, config: SecurityConfig) -> list[SecurityFinding]:
    conn = await asyncpg.connect(uri)
    try:
        user_value = str(await conn.fetchval("SELECT current_user") or "")
        can_create_role = bool(
            await conn.fetchval(
                "SELECT rolsuper OR rolcreaterole FROM pg_roles WHERE rolname = current_user"
            )
        )
    finally:
        await conn.close()

    return [
        SecurityFinding(
            rule_id="DW-SEC-004",
            title="Current database user is not privileged for role administration",
            severity="medium",
            message=f"Current user {user_value!r} should not be superuser/createrole in app-like contexts.",
            query_text="SELECT rolsuper OR rolcreaterole FROM pg_roles WHERE rolname = current_user",
            passed=not can_create_role,
        )
    ]


def _rows_to_list(rows: Any) -> list[Any]:
    if rows is None:
        return []
    if isinstance(rows, list):
        return rows
    return list(rows)


def _finding_log(finding: SecurityFinding) -> str:
    state = "PASS" if finding.passed else "FAIL"
    return f"{finding.rule_id} {state}: {finding.title} - {finding.message}"
