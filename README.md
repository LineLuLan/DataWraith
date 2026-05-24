# DataWraith

> Local PostgreSQL chaos and security testing for developers.

[![CI](https://github.com/LineLuLan/DataWraith/actions/workflows/ci.yml/badge.svg)](https://github.com/LineLuLan/DataWraith/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12%20%7C%203.13-blue.svg)](pyproject.toml)

DataWraith helps you stress-test PostgreSQL behavior before production incidents
happen. It runs locally, produces machine-readable reports, and keeps dangerous
database operations away from production by default.

```bash
python -m pip install -e ".[dev]"
sdb doctor
sdb recipes
sdb quickstart
```

## What v1 can test

- **Concurrency**: update contention, latency, deadlocks, and error rates.
- **R/W heavy workload**: mixed SELECT/INSERT/UPDATE pressure with slow-query
  hints.
- **Migration locks**: DDL-under-load lock pressure with rule-based advice.
- **Security/isolation**: tenant/RLS checks, parameterized SQL injection fuzzing,
  and privilege posture checks.
- **Reports**: JSON, SARIF, JUnit XML, and minimal PDF export.

## Runtime options

DataWraith has two local-only execution modes:

1. **Embedded mode** on Python 3.12 when `pgserver` is available.
2. **Local PostgreSQL fallback** on Python 3.13+ or whenever you prefer a
   user-managed local database.

Start a local database with Docker:

```bash
docker compose up -d postgres
$env:DATAWRAITH_DATABASE_URL="postgresql://datawraith:datawraith@localhost:5432/datawraith"
sdb doctor
```

Then run the v1 smoke flow:

```bash
sdb quickstart --execute --output-dir reports
sdb compare reports/concurrency.json reports/rw-heavy.json
sdb ai analyze reports/migration.json --json
sdb report reports/security.json --format sarif --output reports/security.sarif
sdb report reports/security.json --format junit --output reports/security.xml
sdb report reports/security.json --format pdf --output reports/security.pdf
```

DataWraith rejects non-local PostgreSQL URLs by default. Do **not** point it at
production databases.

## UX shortcuts

If you forget syntax, use:

```bash
sdb recipes     # copy-pasteable commands
sdb quickstart  # guided v1 smoke flow
sdb             # TUI dashboard with command hints
```

## Developer checks

```bash
ruff check .
mypy datawraith
pytest
python -m build
mkdocs build --strict
```

Full docs live in [`docs/`](docs/), especially
[`docs/quickstart.md`](docs/quickstart.md), [`docs/UsageGuide.md`](docs/UsageGuide.md), and [`docs/Architecture.md`](docs/Architecture.md).
