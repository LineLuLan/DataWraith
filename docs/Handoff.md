# DataWraith — Handoff

## Where to start next

1. Read `docs/BuildPlan_Phase1.md`.
2. Install on Python 3.12 for embedded PostgreSQL work.
3. Run `python -m pip install -e ".[dev]"`.
4. Run `sdb doctor`, `pytest`, `ruff check .`, and `mypy datawraith`.
5. For UX-first testing, run `sdb recipes` and `sdb quickstart`; read `docs/UsageGuide.md` for the full step-by-step user testing guide.
6. If using Python 3.12, verify embedded mode with
   `sdb init tests/fixtures/sample_schema.sql --execute`.
7. If using Python 3.13+, start a local PostgreSQL instance and set
   `DATAWRAITH_DATABASE_URL=postgresql://localhost/<db>` or pass
   `--database-url postgresql://localhost/<db>` to execute commands.
   The bundled Docker fallback is
   `docker compose up -d postgres` with
   `postgresql://datawraith:datawraith@localhost:5432/datawraith`.
8. Verify `sdb quickstart --execute --output-dir reports`.
9. Verify `sdb ai analyze reports/migration.json --provider openai` returns advisory output; provider network enrichment remains deferred.
10. Verify `sdb report reports/security.json --format sarif|junit|pdf --output ...` exporters.

## Known limitation

`pgserver` 0.1.4 has no Python 3.13 wheel. Embedded PostgreSQL startup still
requires Python 3.12 until upstream support lands. Python 3.13+ users can run
real execute flows against a user-managed local PostgreSQL instance via
`--database-url` or `DATAWRAITH_DATABASE_URL`; non-local hosts are rejected by
default.

## Latest build slice

- `sdb init schema.sql` parses and summarizes schema files as a dry-run.
- `sdb init schema.sql --execute` is wired to local embedded ShadowDB and persists data under `.datawraith/shadow`; current Python 3.13 runtime cannot verify it because `pgserver` is unavailable.
- `sdb seed --table products --column id:int --rows 10` renders deterministic SQL preview.
- `sdb seed --table products --column id:int --rows 10 --execute` is wired to parameterized psycopg insertion against local ShadowDB; current Python 3.13 runtime cannot verify it because `pgserver` is unavailable.
- `sdb attack concurrency --dry-run` validates config without database execution.
- `sdb attack concurrency --execute --output report.json` is wired to the asyncpg Concurrency Scenario MVP; current Python 3.13 runtime cannot verify it because `pgserver` is unavailable.
- `DataWraith.spec` and `.github/workflows/executable.yml` provide a Windows PyInstaller artifact path; pip remains the primary distribution.
- `sdb compare baseline.json current.json` compares JSON reports for health score, QPS, p95/p99, and error rate; `--json` emits machine-readable deltas.
- `sdb attack --all --execute --output-dir reports/` is wired to run concurrency and rw-heavy sequentially and write per-scenario JSON reports; current Python 3.13 runtime cannot verify it because `pgserver` is unavailable.
- `sdb attack rw-heavy --execute --output rw-heavy.json` is wired to a self-contained ShadowDB workload that prepares product/customer/order seed tables and runs mixed SELECT/INSERT/UPDATE operations; current Python 3.13 runtime cannot verify it because `pgserver` is unavailable.
- `sdb attack rw-heavy --dry-run` validates the Phase 2 config without database execution.
- `sdb attack migration --dry-run` validates the Phase 3 migration config without database execution.
- `sdb attack migration --execute --output migration.json` is wired to a local ShadowDB DDL-under-load simulation; current Python 3.13 runtime cannot verify it because `pgserver` is unavailable.
- `sdb ai setup/status/analyze` is wired for BYOK advisory UX; analyze returns offline rule-based migration suggestions and never auto-applies SQL.
- `sdb attack security --dry-run` validates the Phase 4 security config without database execution.
- `sdb attack security --execute --output security.json` is wired to local ShadowDB tenant/RLS/fuzz/privilege checks; current Python 3.13 runtime cannot verify it because `pgserver` is unavailable.
- `sdb report security.json --format sarif|junit|pdf --output ...` exports existing JSON reports to CI/security-friendly formats.
- `sdb doctor --json` returns machine-readable health checks for automation.
- `sdb init/seed/attack ... --execute --database-url postgresql://localhost/<db>`
  uses a local PostgreSQL fallback instead of embedded `pgserver`.
- `DATAWRAITH_DATABASE_URL=postgresql://localhost/<db>` provides the same
  fallback for repeated commands.
- `docker-compose.yml` starts a local PostgreSQL fallback for contributor E2E
  testing.
- `sdb recipes` and `sdb quickstart` are the recommended UX entrypoints for
  users who do not want to remember long command syntax.
- `docs/UsageGuide.md` now captures detailed CLI usage, report interpretation, and cloud PostgreSQL guidance: Neon/Supabase users should export schema-only metadata and run DataWraith against a local shadow database, not a hosted database URL.
- GitHub Actions CI includes a `postgres-e2e` job that runs Phase 1-4 execute
  flows on Python 3.13 with `DATAWRAITH_E2E_DATABASE_URL`.
- Root `README.md` is intentionally present as the GitHub landing page; other
  long-form docs remain under `docs/`.
- `sdb` opens a minimal Textual dashboard with runtime status, command hints, and report placeholder.
- `tests/test_phase1_e2e.py` captures the target alpha CLI flow and skips when `pgserver` is unavailable.
- `tests/test_phase2_e2e.py` captures the Phase 2 rw-heavy CLI flow and skips when `pgserver` is unavailable.

## Safety reminder

Do not connect DataWraith to production databases. The intended default is a
local embedded shadow PostgreSQL instance. The local PostgreSQL fallback accepts
only localhost/loopback/socket-style URLs unless a future explicit unsafe mode
is designed and documented.
