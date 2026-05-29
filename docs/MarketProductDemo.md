# Market Product Demo

DataWraith includes a small disposable demo project at:

```text
examples/market-product-demo/
```

Use it when you want to show DataWraith with a realistic market/product-management PostgreSQL schema instead of the tiny quickstart table.

## Demo schema

The demo uses five tables:

1. `market_categories`
2. `market_suppliers`
3. `products`
4. `inventory_movements`
5. `market_orders`

`products.stock` is intentionally available as the main concurrency target.

## Fast run

Install DataWraith in development mode first:

```powershell
python -m pip install -e ".[dev]"
sdb doctor
```

If embedded `pgserver` is unavailable, start the local PostgreSQL fallback:

```powershell
docker compose up -d postgres
$env:DATAWRAITH_DATABASE_URL="postgresql://datawraith:datawraith@localhost:5432/datawraith"
sdb doctor
```

Run the demo:

```powershell
.\examples\market-product-demo\run-demo.ps1
```

Or on macOS/Linux/Git Bash:

```bash
bash examples/market-product-demo/run-demo.sh
```

## Manual commands

```powershell
sdb init examples/market-product-demo/schema.sql --execute
sdb init examples/market-product-demo/sample_data.sql --execute
sdb attack concurrency --execute --table products --column stock --duration 10 --workers 4 --updates 80 --output reports/market-demo/concurrency.json
sdb attack rw-heavy --execute --duration 10 --workers 4 --row-count 100 --operations 300 --output reports/market-demo/rw-heavy.json
sdb attack migration --execute --table products --column market_demo_flag --duration 10 --workers 2 --row-count 100 --operations 200 --output reports/market-demo/migration.json
sdb attack security --execute --duration 10 --tenants 3 --rows-per-tenant 5 --fuzz-payloads 8 --output reports/market-demo/security.json
sdb report reports/market-demo/security.json --format pdf --output reports/market-demo/security.pdf
sdb compare reports/market-demo/concurrency.json reports/market-demo/rw-heavy.json
```

## Generated reports

The scripted run writes reports under:

```text
reports/market-demo/
```

Expected files:

```text
concurrency.json
rw-heavy.json
migration.json
security.json
security.sarif
security.xml
security.pdf
```

## Safety

This demo is local-only. For Neon, Supabase, or other hosted PostgreSQL services, export schema-only metadata and test locally instead of running DataWraith directly against a cloud database URL.
