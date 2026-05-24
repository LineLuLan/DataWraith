# DataWraith Usage & Testing Guide

This guide explains how to use DataWraith v1 from a fresh checkout, how to choose a PostgreSQL runtime, and how to interpret the generated reports.

## What DataWraith tests

DataWraith is a local PostgreSQL chaos/security testing CLI. It helps developers test database behavior before production incidents happen.

v1 includes four practical scenarios:

1. **Concurrency**
   - Runs multiple workers against the same table/column.
   - Useful for update contention, lock pressure, deadlocks, latency spikes, and error-rate checks.
2. **R/W heavy workload**
   - Runs mixed `SELECT`, `INSERT`, and `UPDATE` traffic.
   - Useful for CRUD-style workload pressure, QPS, p95/p99 latency, and slow-query hints.
3. **Migration lock**
   - Runs allowlisted DDL while background traffic is active.
   - Useful for checking whether a migration might block real application traffic.
4. **Security/isolation**
   - Creates local multi-tenant fixtures, checks RLS-style tenant isolation, runs safe parameterized SQL injection fuzzing, and reports privilege posture findings.

Report outputs include JSON, SARIF, JUnit XML, and a compact PDF summary.

## Install for local testing

From the repository root:

```powershell
python -m pip install -e ".[dev]"
sdb --version
sdb doctor
```

If you forget the syntax, run:

```powershell
sdb recipes
```

`recipes` is the fastest UX entrypoint. It prints copy-pasteable commands for the most common flows.

## PostgreSQL runtime options

DataWraith tests PostgreSQL behavior. It is not a generic MySQL/MongoDB/SQLite testing tool.

v1 supports two safe local runtime modes.

### Option A: embedded PostgreSQL through pgserver

When `pgserver` is available, DataWraith can start an embedded local PostgreSQL instance automatically.

Check readiness:

```powershell
sdb doctor
```

If doctor reports `pgserver: available`, you can run execute commands without Docker or an external database URL.

Known limitation: `pgserver` 0.1.4 currently has Python 3.12 wheel coverage, but Python 3.13 users may need the local PostgreSQL fallback below.

### Option B: local PostgreSQL fallback through Docker

This is the most reliable way to test on any modern Python version.

Start a local PostgreSQL container:

```powershell
docker compose up -d postgres
```

Set the local database URL:

```powershell
$env:DATAWRAITH_DATABASE_URL="postgresql://datawraith:datawraith@localhost:5432/datawraith"
```

Verify:

```powershell
sdb doctor
```

You should see that the local database URL fallback is configured.

DataWraith intentionally rejects non-local PostgreSQL URLs by default. Do not point it at production databases.

## Quickest full v1 smoke test

Dry-run first:

```powershell
sdb quickstart
```

Run the v1 smoke flow:

```powershell
sdb quickstart --execute --output-dir reports
```

This command does the following:

1. Creates a local quickstart table.
2. Seeds sample data.
3. Runs these scenarios:
   - `concurrency`
   - `rw-heavy`
   - `migration`
   - `security`
4. Writes reports into `reports/`.
5. Exports security reports to SARIF, JUnit XML, and PDF.

Expected outputs:

```text
reports/concurrency.json
reports/rw-heavy.json
reports/migration.json
reports/security.json
reports/security.sarif
reports/security.xml
reports/security.pdf
```

If this flow passes, DataWraith v1 is usable on your machine.

## Recommended new-user flow

```powershell
git clone https://github.com/LineLuLan/DataWraith.git
cd DataWraith
python -m pip install -e ".[dev]"
sdb doctor
sdb recipes
```

If `sdb doctor` says embedded PostgreSQL is unavailable, use Docker fallback:

```powershell
docker compose up -d postgres
$env:DATAWRAITH_DATABASE_URL="postgresql://datawraith:datawraith@localhost:5432/datawraith"
sdb doctor
```

Then run:

```powershell
sdb quickstart --execute --output-dir reports
sdb compare reports/concurrency.json reports/rw-heavy.json
sdb report reports/security.json --format pdf --output reports/security.pdf
```

## Running individual attacks

### Concurrency

Dry-run:

```powershell
sdb attack concurrency --dry-run
```

Execute:

```powershell
sdb attack concurrency --execute --duration 10 --workers 2 --updates 10 --output reports/concurrency.json
```

Useful options:

- `--duration`: scenario duration in seconds.
- `--workers`: concurrent worker count.
- `--updates`: maximum update operations.
- `--table`: target table name.
- `--column`: target numeric column.

Use concurrency testing when you care about update contention, latency spikes, deadlocks, or lock-related errors.

### R/W heavy workload

Dry-run:

```powershell
sdb attack rw-heavy --dry-run --row-count 100 --operations 1000
```

Execute:

```powershell
sdb attack rw-heavy --execute --duration 10 --workers 4 --row-count 100 --operations 1000 --output reports/rw-heavy.json
```

Useful options:

- `--row-count`: number of synthetic rows to prepare.
- `--operations`: operation cap across workers.
- `--read-ratio`: read/write ratio from `0.0` to `1.0`; default is `0.7`.
- `--slow-ms`: slow-query threshold in milliseconds.

Example read-heavy run:

```powershell
sdb attack rw-heavy --execute --read-ratio 0.8 --output reports/rw-heavy.json
```

Use this when you want CRUD-style pressure similar to application traffic.

### Migration lock

Dry-run:

```powershell
sdb attack migration --dry-run
```

Execute:

```powershell
sdb attack migration --execute --duration 10 --workers 2 --output reports/migration.json
```

Tune lock/statement timeouts:

```powershell
sdb attack migration --execute --lock-timeout-ms 500 --statement-timeout-ms 5000 --output reports/migration.json
```

Use this before applying migrations that may lock busy tables.

### Security/isolation

Dry-run:

```powershell
sdb attack security --dry-run
```

Execute:

```powershell
sdb attack security --execute --duration 10 --output reports/security.json
```

Tune tenant/fuzz fixture size:

```powershell
sdb attack security --execute --tenants 3 --rows-per-tenant 10 --fuzz-payloads 8 --output reports/security.json
```

Use this to test local tenant isolation assumptions, RLS-style checks, safe SQL injection fuzzing, and basic privilege posture.

## Run all implemented scenarios

```powershell
sdb attack --all --execute --output-dir reports
```

This writes:

```text
reports/concurrency.json
reports/rw-heavy.json
reports/migration.json
reports/security.json
```

## Compare reports

Human-readable comparison:

```powershell
sdb compare reports/concurrency.json reports/rw-heavy.json
```

Machine-readable comparison:

```powershell
sdb compare reports/concurrency.json reports/rw-heavy.json --json
```

Comparison currently focuses on health score, QPS, p95/p99 latency, and error rate.

## Export reports

Security-friendly SARIF:

```powershell
sdb report reports/security.json --format sarif --output reports/security.sarif
```

CI-friendly JUnit XML:

```powershell
sdb report reports/security.json --format junit --output reports/security.xml
```

Human-readable PDF summary:

```powershell
sdb report reports/security.json --format pdf --output reports/security.pdf
```

## Use a schema file

Preview a schema:

```powershell
sdb init tests/fixtures/sample_schema.sql --dry-run
```

Load it into the local runtime:

```powershell
sdb init tests/fixtures/sample_schema.sql --execute
```

Seed rows:

```powershell
sdb seed --table products --column id:int --column name:name --column stock:int --rows 10 --execute
```

Run an attack against that seeded table:

```powershell
sdb attack concurrency --execute --table products --column stock --output reports/concurrency.json
```

## What if my app uses Neon, Supabase, or another cloud PostgreSQL?

Neon and Supabase are PostgreSQL-compatible services, so DataWraith's PostgreSQL logic is conceptually relevant. However, DataWraith v1 is intentionally **local-only by default**.

That means a direct URL like these should not be used with v1 execute commands:

```text
postgresql://...neon.tech/...
postgresql://...supabase.co/...
```

Reasons:

1. Chaos/load/security tests can create write traffic, locks, latency spikes, and noisy logs.
2. A cloud database might contain real user data.
3. A connection string might point to production by accident.
4. Some scenarios intentionally test stressful behavior that belongs in a disposable shadow database, not a live service.

### Safe workflow for cloud PostgreSQL users

Use a local clone of the schema, not the live cloud database.

Recommended flow:

1. Export schema from your cloud PostgreSQL project.
2. Avoid exporting production user data.
3. Start local PostgreSQL with Docker.
4. Load the schema locally.
5. Seed synthetic data locally.
6. Run DataWraith against the local database.

Example local target:

```powershell
docker compose up -d postgres
$env:DATAWRAITH_DATABASE_URL="postgresql://datawraith:datawraith@localhost:5432/datawraith"
sdb init schema.sql --execute
sdb seed --table products --column id:int --column name:name --column stock:int --rows 100 --execute
sdb attack --all --execute --output-dir reports
```

### Supabase-style workflow

Use Supabase tooling or `pg_dump` to produce a schema-only dump, then run DataWraith locally.

Conceptual flow:

```powershell
# Export schema only from Supabase using your preferred Supabase/pg_dump workflow.
# Save it as schema.sql.

docker compose up -d postgres
$env:DATAWRAITH_DATABASE_URL="postgresql://datawraith:datawraith@localhost:5432/datawraith"
sdb init schema.sql --execute
sdb quickstart --execute --output-dir reports
```

### Neon-style workflow

Neon supports branch-based development databases, but DataWraith v1 still rejects non-local hosts by default. For now, prefer exporting schema and testing locally.

Conceptual flow:

```powershell
# Export schema only from a Neon development branch using pg_dump or your normal Neon workflow.
# Save it as schema.sql.

docker compose up -d postgres
$env:DATAWRAITH_DATABASE_URL="postgresql://datawraith:datawraith@localhost:5432/datawraith"
sdb init schema.sql --execute
sdb attack --all --execute --output-dir reports
```

### Why not allow cloud URLs immediately?

A future version can support an explicit dangerous/advanced mode for disposable remote branches, but it should require strong safeguards first:

- explicit `--allow-remote-shadow` or similar naming;
- repeated confirmation that the target is disposable;
- production-host denylist/allowlist rules;
- read-only schema inspection before write scenarios;
- clear cost/traffic warnings;
- no secrets printed in logs;
- separate docs for Neon/Supabase branch workflows.

Until that exists, the safe answer is: **cloud PostgreSQL schema in, local shadow database out**.

## What if my app does not use PostgreSQL?

DataWraith v1 is PostgreSQL-specific. If your app uses MySQL, SQLite, MongoDB, or another database, DataWraith may still be useful for learning/testing PostgreSQL behavior, but it will not accurately test your production database engine.

Future database adapters could be added later, but they should be separate scenario implementations because concurrency, locks, indexing, isolation, and query planning differ significantly by database.

## How to read the JSON report

A scenario report includes fields like:

- `scenario_type`: which scenario ran.
- `health_score`: high-level score; higher is better.
- `metrics`: raw scenario measurements.
- `culprits`: likely issues or findings.
- `raw_logs`: detailed logs useful for debugging.

Interpretation rule of thumb:

- High health score and low error rate: likely healthy for that local workload.
- High p95/p99 latency: look for lock pressure, slow queries, or overloaded workers.
- Any deadlocks/errors: inspect culprits and raw logs.
- Security findings: review RLS/tenant isolation and privilege assumptions before shipping.

## Maintainer validation commands

Before release or PR merge, run:

```powershell
ruff check .
mypy datawraith
pytest
python -m build
mkdocs build --strict
```

For runtime verification with local PostgreSQL fallback:

```powershell
docker compose up -d postgres
$env:DATAWRAITH_DATABASE_URL="postgresql://datawraith:datawraith@localhost:5432/datawraith"
sdb doctor
sdb quickstart --execute --output-dir reports
```

## Minimal happy path

If you remember only one flow, use this:

```powershell
sdb recipes
sdb quickstart --execute --output-dir reports
sdb compare reports/concurrency.json reports/rw-heavy.json
sdb report reports/security.json --format pdf --output reports/security.pdf
```
