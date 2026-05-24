# DataWraith — Tracker

## Current status

Phase 1 foundation and Phase 2 RW-heavy MVP are implemented in unit-tested code paths. Real embedded PostgreSQL E2E remains gated on Python 3.12 + `pgserver`.

## Done

- Package metadata and console scripts
- CLI `--version` and `doctor`
- Minimal Textual app
- Core Pydantic models
- Scenario ABC and registry
- Scaffold Concurrency scenario
- JSON and ASCII output helpers
- Tests and CI workflow
- Project memory docs
- Schema parser foundation
- Deterministic seed plan and SQL preview
- CLI dry-run commands for `init`, `seed`, and `attack concurrency`
- `ShadowDB.list_tables()` verification helper
- `sdb init --execute` path wired to local embedded ShadowDB data dir
- ShadowDB integration tests skip cleanly when `pgserver` is unavailable
- `SeedResult` model and parameterized `execute_seed_plan()` database insertion path
- `sdb seed --execute` path wired to local embedded ShadowDB data dir
- Concurrency Scenario MVP uses asyncpg workers, tracks QPS/latency/errors/deadlocks, and emits final `ScenarioResult`
- `sdb attack concurrency --execute --output report.json` path wired to local ShadowDB and JSON export
- Minimal useful TUI shows runtime status, ShadowDB path, Concurrency Test command hints, and report placeholder
- `sdb doctor --json` machine-readable health check added
- Phase 1 CLI E2E smoke test added and skips cleanly when `pgserver` is unavailable
- CI now includes `mkdocs build --strict`
- Phase 2 E2E test added and skips cleanly when `pgserver` is unavailable
- Windows PyInstaller spec and manual/PR executable workflow added
- `sdb compare baseline.json current.json` compares health score, QPS, p95/p99, and error rate
- Rule-based slow-query analyzer produces `top_culprits` hints from observed slow query samples
- RW-heavy workload prepares local product/customer/order seed tables and runs mixed SELECT/INSERT/UPDATE workers
- Phase 2 `rw-heavy` scenario registered as `sdb attack rw-heavy`
- `sdb attack --all --execute --output-dir reports/` runs implemented scenarios sequentially and writes per-scenario reports
- `sdb compare --json` emits machine-readable report deltas
- Minimal TUI now shows RW-heavy, attack-all, migration, AI analyze, and compare command hints
- Phase 3 `migration` scenario registered as `sdb attack migration`
- Migration scenario runs local DDL-under-load simulation with lock/statement timeout settings
- Rule-based migration analyzer emits `AISuggestion` records without applying SQL
- `sdb ai setup/status/analyze` BYOK advisory CLI added with OS keyring storage and offline rule-based fallback
- Phase 4 `security` scenario registered as `sdb attack security`
- Security scenario runs local tenant/RLS checks, parameterized injection fuzzing, and privilege posture checks
- `sdb report` exports reports to SARIF, JUnit XML, and minimal PDF
- Minimal TUI now shows security and report export command hints

## Next

- Verify `sdb init --execute` on Python 3.12 with `pgserver` available.
- Verify `sdb seed --execute` on Python 3.12 with `pgserver` available.
- Verify `sdb attack concurrency --execute --output report.json` on Python 3.12 with `pgserver` available.
- Verify `sdb attack rw-heavy --execute --output rw-heavy.json` on Python 3.12 with `pgserver` available.
- Verify `sdb attack migration --execute --output migration.json` on Python 3.12 with `pgserver` available.
- Verify `sdb attack security --execute --output security.json` and `sdb report` exporters on Python 3.12 with `pgserver` available.
- Expand TUI from command-hint dashboard into interactive init/seed/attack screens.
