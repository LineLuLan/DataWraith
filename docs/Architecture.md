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

## Embedded PostgreSQL

`ShadowDB` loads `pgserver` lazily. This keeps imports and CLI health checks
usable on Python versions where `pgserver` wheels are not available yet.
The default CLI execution path stores local embedded PostgreSQL data under
`.datawraith/shadow`, which is gitignored and intended only for development
shadow data.

## Current Python support note

The project code targets Python 3.12+. `pgserver` 0.1.4 currently publishes
wheels through Python 3.12, so Python 3.13 can run scaffold checks but cannot
start embedded PostgreSQL until upstream support exists.
