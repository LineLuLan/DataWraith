# DataWraith — Tracker

## Current status

Initial scaffold implemented and first Phase 1 engine slice started.

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

## Next

- Verify `sdb init --execute` on Python 3.12 with `pgserver` available.
- Verify `sdb seed --execute` on Python 3.12 with `pgserver` available.
- Verify `sdb attack concurrency --execute --output report.json` on Python 3.12 with `pgserver` available.
- Expand TUI from command-hint dashboard into interactive init/seed/attack screens.
