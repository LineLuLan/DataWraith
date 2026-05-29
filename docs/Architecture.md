# DataWraith — Architecture

## Layers

1. **Interface**: Typer CLI and Textual TUI.
2. **Output**: JSON export and ASCII rendering.
3. **Engine**: scenario registry and streaming `ScenarioEvent` contracts.
4. **Core**: Pydantic models, exceptions, config, logging, and `ShadowDB`.

## Public contracts

- `Scenario.validate_config() -> list[str]`
- `Scenario.run() -> AsyncIterator[ScenarioEvent]`
- Final scenario event must be `EventType.COMPLETED` once a scenario implementation is complete.
- JSON exporter writes `ScenarioResult.model_dump(mode="json")`.
- Schema parser summarizes DDL and rejects obviously dangerous statements before future execution paths.
- Seeder produces deterministic preview rows/SQL and has a parameterized psycopg insertion path for local ShadowDB; high-volume COPY optimization is deferred.
- Concurrency Scenario MVP uses asyncpg connections per worker, conservative local defaults, and reports QPS, latency percentiles, errors, and deadlocks.
- RW Heavy Scenario uses embedded ShadowDB, prepares local product/customer/order-style seed tables, runs a mixed SELECT/INSERT/UPDATE asyncpg workload, and reports QPS, latency percentiles, errors, and rule-based slow-query culprits.
- Migration Scenario prepares a local table, runs background SELECT/UPDATE workload, executes allowlisted DDL with lock/statement timeouts, and reports lock pressure.
- `sdb attack --all --execute --output-dir reports/` runs implemented scenarios sequentially and writes one JSON report per scenario.
- `sdb compare baseline.json current.json` validates two `ScenarioResult` JSON reports and compares health score, QPS, p95/p99 latency, and error rate; `--json` emits machine-readable deltas.
- AI advisory is offline-first in Phase 3: OS keyring BYOK setup, deterministic rule-based migration suggestions, no network call, and no auto-applied SQL.
- Security Scenario prepares local multi-tenant fixtures, checks RLS/tenant isolation, runs parameterized SQL injection fuzzing, and reports security findings.
- `sdb report` exports JSON reports to SARIF, JUnit XML, and minimal PDF formats for CI/security workflows.
- TUI currently acts as a command dashboard: runtime status, default ShadowDB path, scenario command hints, compare hints, and a report placeholder.

## PostgreSQL runtime

`ShadowDB` supports two local-only runtime modes:

1. **Embedded mode**: load `pgserver` lazily and store local PostgreSQL data
   under `.datawraith/shadow`, which is gitignored and intended only for
   development shadow data.
2. **Local PostgreSQL fallback**: accept `--database-url` or
   `DATAWRAITH_DATABASE_URL` when the URL targets localhost/loopback or a local
   socket. Non-local hosts are rejected by default so chaos scenarios are not
   accidentally pointed at production infrastructure.

This keeps the project easy to try on Python 3.13+ while preserving the
zero-Docker embedded path for Python versions where `pgserver` wheels exist.

## Current Python support note

The project code targets Python 3.12+. `pgserver` 0.1.4 currently publishes
wheels through Python 3.12, so Python 3.13 cannot start embedded PostgreSQL
until upstream support exists. Python 3.13 users can still run real execute
flows against a local user-managed PostgreSQL instance via `--database-url` or
`DATAWRAITH_DATABASE_URL`.

## Durable Technical Decisions

- **Scaffold before full engine**: package metadata, contracts, docs, CI, and minimal UI/CLI were created before deep scenario work so module ownership and public contracts stayed stable.
- **Lazy `pgserver` runtime**: `pgserver` is optional and loaded lazily because current wheels cover Python 3.12 but not Python 3.13 embedded startup.
- **Dry-run primitives first**: schema parsing, seed planning, and CLI dry-runs remain useful on runtimes where embedded PostgreSQL is unavailable.
- **Local PostgreSQL fallback**: execute commands may use `--database-url` or `DATAWRAITH_DATABASE_URL` only for localhost/loopback/socket targets so Python 3.13+ users can run real flows safely.
- **Cloud PostgreSQL safety**: Neon, Supabase, and other hosted PostgreSQL providers are conceptually compatible, but v1 does not run chaos/security scenarios directly against non-local URLs; users should export schema-only metadata into a local shadow DB.
- **Offline-first AI advisory**: BYOK setup/status and `sdb ai analyze` use deterministic rule-based suggestions first; provider-backed network enrichment and auto-applied SQL are deferred.
- **Local-only security/reporting**: security/isolation checks and SARIF/JUnit/PDF exports are designed for local shadow databases and CI-friendly artifacts, not production writes.
- **Market-product demo**: `examples/market-product-demo/` exists as a synthetic five-table PostgreSQL showcase for GitHub visitors and testers without weakening production/cloud safety constraints.
