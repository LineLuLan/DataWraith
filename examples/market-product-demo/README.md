# Market Product Management Demo

This is a small disposable PostgreSQL project for testing and demonstrating DataWraith.

It models a simple market/product-management system with five tables:

1. `market_categories`
2. `market_suppliers`
3. `products`
4. `inventory_movements`
5. `market_orders`

The demo is intentionally local-only. Do not run DataWraith chaos/security scenarios against production or hosted databases directly.

## What this demo shows

- Loading a realistic schema into a local shadow PostgreSQL runtime.
- Seeding product/catalog/order-style data.
- Running DataWraith concurrency testing against `products.stock`.
- Running R/W-heavy workload pressure.
- Running migration-lock and security/isolation scenarios.
- Exporting JSON, SARIF, JUnit XML, and PDF reports.

## Prerequisites

From the DataWraith repository root:

```powershell
python -m pip install -e ".[dev]"
sdb doctor
```

If embedded `pgserver` is unavailable, use local PostgreSQL fallback:

```powershell
docker compose up -d postgres
$env:DATAWRAITH_DATABASE_URL="postgresql://datawraith:datawraith@localhost:5432/datawraith"
sdb doctor
```

## Fast demo on Windows PowerShell

```powershell
.\examples\market-product-demo\run-demo.ps1
```

Optional low-worker run:

```powershell
.\examples\market-product-demo\run-demo.ps1 -Duration 10 -Workers 2 -OutputDir reports\market-demo
```

## Fast demo on macOS/Linux/Git Bash

```bash
bash examples/market-product-demo/run-demo.sh
```

## Manual step-by-step flow

Load the schema:

```powershell
sdb init examples/market-product-demo/schema.sql --execute
```

Load sample rows:

```powershell
sdb init examples/market-product-demo/sample_data.sql --execute
```

Run concurrency against the market products table:

```powershell
sdb attack concurrency --execute --table products --column stock --duration 10 --workers 4 --updates 80 --output reports/market-demo/concurrency.json
```

Run R/W-heavy workload:

```powershell
sdb attack rw-heavy --execute --duration 10 --workers 4 --row-count 100 --operations 300 --output reports/market-demo/rw-heavy.json
```

Run migration-lock test:

```powershell
sdb attack migration --execute --table products --column market_demo_flag --duration 10 --workers 2 --row-count 100 --operations 200 --output reports/market-demo/migration.json
```

Run security/isolation test:

```powershell
sdb attack security --execute --duration 10 --tenants 3 --rows-per-tenant 5 --fuzz-payloads 8 --output reports/market-demo/security.json
```

Export security reports:

```powershell
sdb report reports/market-demo/security.json --format sarif --output reports/market-demo/security.sarif
sdb report reports/market-demo/security.json --format junit --output reports/market-demo/security.xml
sdb report reports/market-demo/security.json --format pdf --output reports/market-demo/security.pdf
```

Compare performance reports:

```powershell
sdb compare reports/market-demo/concurrency.json reports/market-demo/rw-heavy.json
```

## Expected report files

```text
reports/market-demo/concurrency.json
reports/market-demo/rw-heavy.json
reports/market-demo/migration.json
reports/market-demo/security.json
reports/market-demo/security.sarif
reports/market-demo/security.xml
reports/market-demo/security.pdf
```

## Cloud database note

If your real app uses Neon, Supabase, Railway, Render, or another hosted PostgreSQL provider, export a schema-only dump and run this demo locally. DataWraith v1 rejects non-local database URLs by default because the scenarios create intentional load, writes, and lock pressure.
