# DataWraith — Build Plan All Phases

This file is the cross-phase execution map. Use `docs/BuildPlan_Phase1.md` for
the current detailed Phase 1 implementation checklist, and use this file to
understand what remains after v0.1.

## Current verification gate — pgserver

Current local state:

- Active `python`: 3.13.0
- Windows launcher: Python 3.11 only
- `pgserver`: unavailable on current runtime

DataWraith can only claim real embedded PostgreSQL verification after a Python
3.12 runtime with `pgserver` available is installed.

Required verification commands:

```bash
python --version
sdb doctor
pytest tests/test_shadow_db.py tests/test_seeder_integration.py tests/test_concurrency.py tests/test_phase1_e2e.py
sdb init tests/fixtures/sample_schema.sql --execute
sdb seed --table products --column id:int --column name:name --column stock:int --rows 10 --execute
sdb attack concurrency --execute --duration 10 --workers 2 --updates 10 --output report.json
python -m json.tool report.json
```

Expected status before real E2E release claims:

- Python 3.12.x
- `pgserver: available`
- all real DB integration tests pass
- `report.json` contains `scenario_type=concurrency` and non-zero `qps_avg`

Phase 2 code may continue behind skipped real-DB tests, but DataWraith must not
claim Phase 1 or Phase 2 real embedded PostgreSQL E2E verification until this
gate passes.

## Phase 1 — v0.1 Concurrency Foundation

Goal: ship the first usable local alpha for PostgreSQL concurrency testing.

Already implemented:

- Package scaffold and entrypoints.
- Core Pydantic contracts.
- `ShadowDB` wrapper and local data directory.
- Schema parser and dry-run/execute init path.
- Deterministic seed preview and parameterized insert path.
- Concurrency Scenario MVP with asyncpg workers.
- JSON report export and ASCII summary.
- Minimal Textual dashboard.
- CI lint/type/test/build/docs checks.
- E2E tests that skip cleanly when `pgserver` is unavailable.

Remaining before v0.1-alpha:

1. Verify Python 3.12 + `pgserver` real DB flow.
2. Fix any runtime issues in:
   - `ShadowDB.start()`
   - `sdb init --execute`
   - `sdb seed --execute`
   - `sdb attack concurrency --execute --output`
3. Add README quickstart examples with real output snippets.
4. Record one local demo flow.

Definition of done:

- `pip install -e ".[dev]"` works on Python 3.12.
- Phase 1 CLI E2E passes.
- TUI opens without errors.
- CI passes on Python 3.12 and 3.13.
- Docs clearly state Python 3.13 pgserver limitation if still true.

## Phase 2 — v0.2 R/W Heavy + Headless + Executable

Goal: add read/write-heavy workload and make DataWraith more useful in CI/local
automation.

Build slices:

1. **RW Heavy config and scenario contract**
   - Add `RWHeavyConfig` fields needed for workload scale, read/write ratio,
     joins, and row count.
   - Register `rw-heavy` in scenario registry.
   - Add tests for config validation and registry behavior.

2. **Read/write workload MVP**
   - Seed larger synthetic product/order/customer-style dataset.
   - Run mixed SELECT/INSERT/UPDATE workload with configurable ratio.
   - Track QPS, latency percentiles, errors, slow query samples.
   - Keep defaults safe for laptops.

3. **Basic slow-query/full-scan analysis**
   - Start rule-based analyzer from available query timings.
   - Add optional EXPLAIN collection where safe.
   - Defer deep pg_qualstats integration until extension availability is proven.

4. **Headless CLI polish**
   - Support:
     ```bash
     sdb attack rw-heavy --execute --output rw-heavy.json
     sdb attack --all --execute --output-dir reports/
     ```
   - Status: `--all` and `--output-dir` are implemented; real DB E2E remains pgserver-gated.
   - Ensure non-zero exits on failed scenarios.
   - Keep JSON report stable.

5. **Compare runs**
   - Implement:
     ```bash
     sdb compare baseline.json current.json
     ```
   - Compare health score, QPS, p95/p99, error rate, and top culprits.
   - Output console summary and optional JSON.
   - Status: console and `--json` output are implemented.

6. **PyInstaller executable**
   - Add build workflow for Windows executable.
   - Use a checked-in PyInstaller spec and collect DataWraith hidden imports.
   - Treat executable as secondary distribution; pip remains primary.

Phase 2 acceptance:

```bash
sdb attack rw-heavy --execute --duration 10 --workers 2 --row-count 10 --operations 20 --output rw-heavy.json
sdb compare baseline.json rw-heavy.json
python -m build
pytest
```

Current implementation status: RW-heavy MVP, compare command, rule-based
analyzer, PyInstaller spec, and executable workflow are implemented and covered
by unit tests. Real DB E2E remains skipped on the current Python 3.13 runtime
because `pgserver` is unavailable.

## Phase 3 — v0.3 Migration Lock + AI BYOK

Goal: simulate migration risk under load and add optional AI analysis without
making AI foundational.

Build slices:

1. **Migration config and scenario**
   - Add `MigrationConfig`.
   - Register `migration`.
   - Support safe DDL examples:
     - `ALTER TABLE ... ADD COLUMN`
     - `CREATE INDEX`
     - lock-timeout simulation

2. **Workload + DDL runner**
   - Run background read/write workload.
   - Execute DDL under load.
   - Track blocked queries, timeout count, migration duration, and estimated
     downtime.

3. **Migration result analysis**
   - Add rule-based suggestions:
     - use concurrent index creation where applicable
     - split heavy migrations
     - add lock timeout
     - perform backfill in batches

4. **AI BYOK bridge**
   - Add provider-neutral `analyze(result, provider, api_key)` contract.
   - Store keys through OS keyring only.
   - No shipped keys, no telemetry, no auto-apply.

5. **AI UX**
   - CLI:
     ```bash
     sdb ai setup
     sdb ai analyze report.json
     ```
   - TUI: optional AI suggestion panel.

Phase 3 acceptance:

```bash
sdb attack migration --execute --output migration.json
sdb ai analyze migration.json --provider openai
pytest
```

## Phase 4 — v1.0 Security & Isolation + Reports

Goal: complete the four-scenario OSS v1.0 and add CI-friendly reporting.

Build slices:

1. **Security config and scenario**
   - Add `SecurityConfig`.
   - Register `security`.
   - Keep it local-only against ShadowDB.

2. **RLS and tenant isolation checks**
   - Generate multi-tenant fixtures.
   - Verify tenant scoping assumptions.
   - Detect cross-tenant result leakage.

3. **SQL injection fuzz MVP**
   - Provide safe local fuzz cases.
   - Do not execute against external DBs.
   - Report failed sanitization assumptions.

4. **Privilege escalation checks**
   - Test local role grants/denies where embedded PostgreSQL supports it.
   - Report misconfigured access patterns.

5. **Multi-format reports**
   - SARIF for GitHub Security tab.
   - JUnit XML for CI.
   - PDF only after JSON/SARIF/JUnit are stable.

6. **v1.0 release readiness**
   - Full docs.
   - Demo GIF.
   - Changelog.
   - Cross-platform CI.
   - Public launch assets.

Phase 4 acceptance:

```bash
sdb attack security --execute --output security.json
sdb report security.json --format sarif --output security.sarif
sdb report security.json --format junit --output security.xml
pytest
```

## Phase 5+ — Optional Future

Only start after v1.0:

- MCP server.
- Multi-DB support.
- Hosted CI runner.
- Subscription tier.
- Advanced AI workflow with human approval gates.

## Cross-phase rules

- Do not support production/external DB writes by default.
- Default all risky DB work to embedded ShadowDB.
- Keep AI opt-in and advisory only.
- Keep pip as primary distribution.
- Keep all Markdown docs in `docs/`.
- Update `docs/Tracker.md` and `docs/Handoff.md` after every meaningful change.
