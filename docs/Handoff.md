# DataWraith — Handoff

## Where to start next

1. Read `docs/BuildPlan_Phase1.md`.
2. Install on Python 3.12 for embedded PostgreSQL work.
3. Run `python -m pip install -e ".[dev]"`.
4. Run `sdb doctor`, `pytest`, `ruff check .`, and `mypy datawraith`.
5. Verify `sdb init tests/fixtures/sample_schema.sql --execute` on Python 3.12 with `pgserver` available.
6. Verify `sdb seed --table products --column id:int --column name:name --rows 5 --execute` on Python 3.12 with `pgserver` available.
7. Verify `sdb attack concurrency --execute --output report.json` on Python 3.12 with `pgserver` available.
8. On Python 3.13, continue with interactive TUI screens or CLI UX polish that does not require real `pgserver`.

## Known limitation

`pgserver` 0.1.4 has no Python 3.13 wheel. The scaffold remains importable on
Python 3.13, but embedded PostgreSQL startup requires Python 3.12 until upstream
support lands.

## Latest build slice

- `sdb init schema.sql` parses and summarizes schema files as a dry-run.
- `sdb init schema.sql --execute` is wired to local embedded ShadowDB and persists data under `.datawraith/shadow`; current Python 3.13 runtime cannot verify it because `pgserver` is unavailable.
- `sdb seed --table products --column id:int --rows 10` renders deterministic SQL preview.
- `sdb seed --table products --column id:int --rows 10 --execute` is wired to parameterized psycopg insertion against local ShadowDB; current Python 3.13 runtime cannot verify it because `pgserver` is unavailable.
- `sdb attack concurrency --dry-run` validates config without database execution.
- `sdb attack concurrency --execute --output report.json` is wired to the asyncpg Concurrency Scenario MVP; current Python 3.13 runtime cannot verify it because `pgserver` is unavailable.
- `sdb doctor --json` returns machine-readable health checks for automation.
- `sdb` opens a minimal Textual dashboard with runtime status, command hints, and report placeholder.
- `tests/test_phase1_e2e.py` captures the target alpha CLI flow and skips when `pgserver` is unavailable.

## Safety reminder

Do not connect DataWraith to production databases. The intended default is a
local embedded shadow PostgreSQL instance.
