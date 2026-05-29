# Quickstart

```bash
python -m pip install datawraith
sdb
sdb recipes
sdb quickstart
```

For local development:

```bash
python -m pip install -e ".[dev]"
sdb doctor
sdb doctor --json
pytest
```


Phase 1 dry-run:

```bash
sdb quickstart
sdb init tests/fixtures/sample_schema.sql
sdb seed --table products --column id:int --column name:name --column stock:int --rows 10
sdb attack concurrency --dry-run
```

Phase 2 dry-run and report comparison:

```bash
sdb attack rw-heavy --dry-run --row-count 10 --operations 20
sdb attack --all --dry-run --row-count 10 --operations 20
sdb attack migration --dry-run --migration-operation add_column
sdb attack security --dry-run
sdb compare baseline.json current.json
sdb compare baseline.json current.json --json
```

Real execution has two local-only paths:

1. Python 3.12 embedded mode with `pgserver` available.
2. Python 3.13+ local PostgreSQL fallback through `--database-url` or
   `DATAWRAITH_DATABASE_URL`.

Embedded mode:

```bash
sdb init tests/fixtures/sample_schema.sql --execute
sdb seed --table products --column id:int --column name:name --column stock:int --rows 10 --execute
sdb attack concurrency --execute --duration 10 --workers 2 --updates 10 --output report.json
sdb attack rw-heavy --execute --duration 10 --workers 2 --row-count 10 --operations 20 --output rw-heavy.json
sdb attack --all --execute --duration 10 --workers 2 --row-count 10 --operations 20 --output-dir reports/
sdb attack migration --execute --duration 10 --workers 2 --row-count 10 --operations 20 --output migration.json
sdb ai analyze migration.json --provider openai
sdb attack security --execute --duration 10 --tenants 2 --rows-per-tenant 2 --output security.json
sdb report security.json --format sarif --output security.sarif
sdb report security.json --format junit --output security.xml
sdb report security.json --format pdf --output security.pdf
```

Local PostgreSQL fallback:

```bash
docker compose up -d postgres
$env:DATAWRAITH_DATABASE_URL="postgresql://localhost/datawraith"
sdb quickstart --execute --output-dir reports
```

The bundled `docker-compose.yml` starts PostgreSQL with
`postgresql://datawraith:datawraith@localhost:5432/datawraith`.

DataWraith rejects non-local PostgreSQL hosts by default. Do not point the tool
at production databases.

## Detailed usage guide

For a full step-by-step testing walkthrough, report interpretation, and guidance
for Neon/Supabase/cloud PostgreSQL users, see `docs/UsageGuide.md`.

Cloud PostgreSQL services such as Neon and Supabase are PostgreSQL-compatible,
but DataWraith v1 intentionally rejects non-local hosts by default. Export a
schema-only dump and test it against a local shadow PostgreSQL instance instead
of running chaos/security scenarios directly against a hosted database.
