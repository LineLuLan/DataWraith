# Quickstart

```bash
python -m pip install datawraith
sdb
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
sdb init tests/fixtures/sample_schema.sql
sdb seed --table products --column id:int --column name:name --column stock:int --rows 10
sdb attack concurrency --dry-run
```

Phase 2 dry-run and report comparison:

```bash
sdb attack rw-heavy --dry-run --row-count 10 --operations 20
sdb compare baseline.json current.json
```

Real embedded PostgreSQL execution requires Python 3.12 with `pgserver`
available:

```bash
sdb init tests/fixtures/sample_schema.sql --execute
sdb seed --table products --column id:int --column name:name --column stock:int --rows 10 --execute
sdb attack concurrency --execute --duration 10 --workers 2 --updates 10 --output report.json
sdb attack rw-heavy --execute --duration 10 --workers 2 --row-count 10 --operations 20 --output rw-heavy.json
```
