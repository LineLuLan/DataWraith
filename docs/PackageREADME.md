# DataWraith

PostgreSQL chaos-testing tool for local shadow databases. DataWraith is
engine-first, pip-installable, MIT licensed, and designed to stress-test
PostgreSQL with an embedded runtime when available, or with a safe local
PostgreSQL fallback on newer Python versions.

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
- Safe local PostgreSQL fallback via `--database-url` /
  `DATAWRAITH_DATABASE_URL` when embedded `pgserver` is unavailable

Real embedded PostgreSQL E2E requires Python 3.12 with `pgserver` available.
Python 3.13+ users can run the same execute flows against a local PostgreSQL
instance.

## Developer quickstart

```bash
python -m pip install -e ".[dev]"
sdb --version
sdb doctor
sdb recipes
sdb quickstart
pytest
ruff check .
mypy datawraith
```

> Note: `pgserver` currently publishes wheels through Python 3.12. On Python
> 3.13+, use `--database-url postgresql://localhost/<db>` or set
> `DATAWRAITH_DATABASE_URL=postgresql://localhost/<db>` to run against a local
> PostgreSQL instance. DataWraith rejects non-local hosts by default.

Optional local PostgreSQL fallback:

```bash
docker compose up -d postgres
$env:DATAWRAITH_DATABASE_URL="postgresql://datawraith:datawraith@localhost:5432/datawraith"
sdb doctor
```

## CLI

```bash
sdb                 # open the Textual TUI
sdb --version       # show package version
sdb doctor          # local environment health check
sdb doctor --json   # machine-readable health check
sdb recipes         # copy-paste command recipes
sdb quickstart      # guided dry-run tour
sdb quickstart --execute --output-dir reports
sdb init schema.sql # parse schema dry-run
sdb init schema.sql --execute --database-url postgresql://localhost/datawraith
sdb seed --table products --column id:int --column name:name --rows 10
sdb attack concurrency
sdb attack concurrency --execute --output report.json
sdb attack concurrency --execute --database-url postgresql://localhost/datawraith --output report.json
sdb attack rw-heavy --dry-run
sdb attack rw-heavy --execute --duration 10 --workers 2 --row-count 100 --operations 1000 --output rw-heavy.json
sdb compare report.json rw-heavy.json
sdb compare report.json rw-heavy.json --json
sdb attack --all --execute --output-dir reports/
sdb attack migration --dry-run --migration-operation add_column
sdb ai analyze migration.json --provider openai
sdb attack security --dry-run
sdb report security.json --format sarif --output security.sarif
python -m datawraith --version
```

## Project docs

- `docs/ProjectBrief.md` ? product source of truth summary
- `docs/Architecture.md` ? architecture, contracts, and durable decisions
- `docs/ACTIVE_STATE.md` ? current backlog, validation gaps, risks, and next execution gate
- `docs/BuildPlan_Phase1.md` ? historical file-level build roadmap
- `docs/DataWraith_Brief.md` / `docs/DataWraith_Blueprint_E2E.md` ? original source docs
