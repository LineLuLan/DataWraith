# DataWraith

PostgreSQL chaos-testing tool for local shadow databases. DataWraith is
engine-first, pip-installable, MIT licensed, and designed to stress-test
PostgreSQL without Docker or a system PostgreSQL install.

```bash
pip install datawraith
sdb
```

## Current focus

The first release targets the Concurrency Test foundation and the Phase 2 branch adds RW-heavy workload primitives:

- Python package + `sdb` CLI entrypoint
- Embedded PostgreSQL wrapper through `pgserver`
- Engine contracts for streaming scenario events
- Textual TUI scaffold
- JSON report export contract
- RW-heavy mixed SELECT/INSERT/UPDATE workload MVP
- JSON report comparison via `sdb compare`

Real embedded PostgreSQL E2E requires Python 3.12 with `pgserver` available.

## Developer quickstart

```bash
python -m pip install -e ".[dev]"
sdb --version
sdb doctor
pytest
ruff check .
mypy datawraith
```

> Note: `pgserver` currently publishes wheels through Python 3.12. On Python
> 3.13, `sdb doctor` reports embedded PostgreSQL as unavailable until upstream
> ships a compatible wheel.

## CLI

```bash
sdb                 # open the Textual TUI
sdb --version       # show package version
sdb doctor          # local environment health check
sdb doctor --json   # machine-readable health check
sdb init schema.sql # parse schema dry-run
sdb seed --table products --column id:int --column name:name --rows 10
sdb attack concurrency
sdb attack concurrency --execute --output report.json
sdb attack rw-heavy --dry-run
sdb attack rw-heavy --execute --duration 10 --workers 2 --row-count 100 --operations 1000 --output rw-heavy.json
sdb compare report.json rw-heavy.json
sdb compare report.json rw-heavy.json --json
sdb attack --all --execute --output-dir reports/
sdb attack migration --dry-run --migration-operation add_column
sdb ai analyze migration.json --provider openai
python -m datawraith --version
```

## Project docs

- `docs/ProjectBrief.md` — product source of truth summary
- `docs/Architecture.md` — scaffold architecture and contracts
- `docs/BuildPlan_Phase1.md` — detailed file-level build roadmap
- `docs/Roadmap.md` — phase roadmap
- `docs/Tracker.md` — current implementation status
- `docs/Handoff.md` — next-agent handoff
- `docs/Decisions.md` — decisions and tradeoffs
- `docs/DataWraith_Brief.md` / `docs/DataWraith_Blueprint_E2E.md` — original source docs
