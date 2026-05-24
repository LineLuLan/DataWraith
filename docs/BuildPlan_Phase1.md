# DataWraith — Phase 1 Build Plan

This is the file-level execution plan for future sessions. Start here after
reading `docs/ProjectBrief.md`, `docs/Architecture.md`, `docs/Tracker.md`, and
`docs/Handoff.md`.

## Current target

Build a local v0.1-alpha flow:

```bash
sdb init tests/fixtures/sample_schema.sql --execute
sdb seed --table products --column id:int --column name:name --column stock:int --rows 1000 --execute
sdb attack concurrency --duration 10 --workers 20 --output report.json
```

The first usable alpha must parse schema, start embedded PostgreSQL, load schema,
seed data, run a real concurrency workload, and export JSON.

## Runtime gate

Embedded PostgreSQL work requires Python 3.12 until `pgserver` ships Python 3.13
wheels. On Python 3.13, keep implementing unit-testable code paths and dry-runs,
but do not claim real `pgserver` verification.

Acceptance:

```bash
python --version
sdb doctor
```

Expected for DB integration:

```text
Python 3.12.x
pgserver: available
```

## Slice 1 — ShadowDB execution path

Status: implemented in code with integration test skip when `pgserver` is
unavailable. Still needs real Python 3.12 verification.

Files:

- `datawraith/core/shadow_db.py`
- `tests/test_shadow_db.py`
- `tests/fixtures/sample_schema.sql`

Build:

- Verify `ShadowDB.start()` and `ShadowDB.stop()` against real `pgserver`.
- Verify `load_schema(sql)` creates tables.
- Add `list_tables()` or a small verification helper if needed by CLI.
- Keep temp directory cleanup safe and local-only.
- Add pytest skip when `pgserver` is unavailable.

Acceptance:

```bash
pytest tests/test_shadow_db.py
```

## Slice 2 — `sdb init --execute`

Status: command path implemented. On Python 3.13 it fails gracefully because
`pgserver` is unavailable; verify on Python 3.12 before marking complete.

Files:

- `datawraith/cli.py`
- `datawraith/engine/schema_parser.py`
- `datawraith/core/shadow_db.py`
- `tests/test_cli.py`
- `tests/test_schema_parser.py`

Build:

- Keep `sdb init schema.sql` as default dry-run.
- Add `sdb init schema.sql --execute` to start embedded PostgreSQL and load schema.
- Print statement count and tables discovered.
- Do not support external database URIs in Phase 1.

Acceptance:

```bash
sdb init tests/fixtures/sample_schema.sql
sdb init tests/fixtures/sample_schema.sql --execute
pytest tests/test_cli.py tests/test_schema_parser.py
```

## Slice 3 — Seeder execution

Status: implemented in code with integration test skip when `pgserver` is
unavailable. Still needs real Python 3.12 verification after `sdb init
--execute`.

Files:

- `datawraith/engine/seeder.py`
- `datawraith/core/types.py`
- `datawraith/cli.py`
- `tests/test_seeder.py`
- `tests/test_seeder_integration.py`

Build:

- Add `SeedResult` model with table, requested rows, inserted rows, and duration.
- Keep deterministic preview generation.
- Add database execution for small batches using parameterized psycopg inserts.
- Defer COPY optimization until basic execution is stable.
- Validate identifiers; never concatenate untrusted values as literals.

Acceptance:

```bash
sdb seed --table products --column id:int --column name:name --rows 5
sdb seed --table products --column id:int --column name:name --rows 5 --execute
pytest tests/test_seeder.py tests/test_seeder_integration.py
```

## Slice 4 — Concurrency scenario MVP

Status: MVP implemented with asyncpg workers and skipped real-DB integration
test when `pgserver` is unavailable. Still needs Python 3.12 verification.

Files:

- `datawraith/engine/scenarios/concurrency.py`
- `datawraith/engine/runner.py`
- `datawraith/core/types.py`
- `tests/test_scenario_contract.py`
- `tests/test_concurrency.py`

Build:

- Replace scaffold-only run with real asyncpg workers.
- Configurable duration, workers, target table, target column.
- Run concurrent `UPDATE` operations against seeded rows.
- Track completed operations, errors, latency p50/p95/p99, qps avg/max, and deadlock count.
- Yield `STARTED`, `LOG`, `METRIC`, `WARNING`/`ERROR`, and final `COMPLETED`.
- Keep workload conservative by default for local machines.

Acceptance:

```bash
sdb attack concurrency --duration 10 --workers 20 --output report.json
pytest tests/test_concurrency.py
```

## Slice 5 — JSON report and CLI E2E

Status: `sdb attack concurrency --execute --output report.json` is wired and
unit-tested with fake execution. Still needs Python 3.12 real-DB E2E.

Files:

- `datawraith/cli.py`
- `datawraith/output/json_exporter.py`
- `datawraith/output/ascii_renderer.py`
- `tests/test_output.py`
- `tests/test_cli.py`

Build:

- Add `--output report.json` to `sdb attack concurrency`.
- Collect the final `ScenarioResult`.
- Export JSON through `JSONExporter`.
- Print ASCII summary through `render_result()`.
- Return non-zero exit code on config or scenario errors.

Acceptance:

```bash
sdb attack concurrency --duration 10 --workers 20 --output report.json
python -m json.tool report.json
```

## Slice 6 — Minimal useful TUI

Status: minimal command-hint dashboard implemented. Interactive init/seed/attack
screens are still future polish after Python 3.12 DB verification.

Files:

- `datawraith/tui/app.py`
- `datawraith/tui/theme.py`
- `datawraith/tui/screens/*`
- `datawraith/tui/widgets/*`
- `tests/test_tui/*`

Build:

- Add splash screen.
- Add simple attack screen for Concurrency Test.
- Render live log/metric events.
- Render final report summary.
- Keep design simple; polish animation later.

Acceptance:

```bash
sdb
```

Manual check:

- App opens.
- Title and version render.
- No console error.
- User can reach a Concurrency Test/report surface.

## Slice 7 — CI and release readiness

Status: CI includes lint, typecheck, tests, package build, and strict docs build.
Release readiness still depends on Python 3.12 `pgserver` E2E verification.

Files:

- `.github/workflows/ci.yml`
- `pyproject.toml`
- `docs/PackageREADME.md`
- `docs/quickstart.md`
- `docs/Tracker.md`
- `docs/Handoff.md`

Build:

- Keep Python 3.12 and 3.13 matrix.
- Mark real `pgserver` tests as Python 3.12-only/skipped when unavailable.
- Keep `ruff`, `mypy`, `pytest`, and `python -m build` green.
- Update docs after every behavior/API change.

Acceptance:

```bash
ruff check .
mypy datawraith
pytest
python -m build
mkdocs build --strict
```

## Definition of done for v0.1-alpha

- CLI E2E runs locally with embedded PostgreSQL on Python 3.12.
- JSON report is generated and validates as JSON.
- Unit tests pass on Python 3.12 and 3.13.
- DB integration tests pass on Python 3.12 or skip with clear reason elsewhere.
- Docs in `docs/` explain current commands and known limitations.
