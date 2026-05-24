# DataWraith - Phase 2 Build Plan

This file captures the current Phase 2 implementation and the remaining gate to
verify it against real embedded PostgreSQL.

## Current target

```bash
sdb attack rw-heavy --execute --duration 10 --workers 2 --row-count 10 --operations 20 --output rw-heavy.json
sdb compare report.json rw-heavy.json
python -m json.tool rw-heavy.json
```

## Runtime gate

Phase 2 uses the same embedded PostgreSQL dependency as Phase 1. On the current
local Python 3.13 runtime, `pgserver` is unavailable, so real DB E2E tests are
skipped and must not be claimed as verified.

Required environment for real E2E:

```bash
python --version  # Python 3.12.x
sdb doctor        # pgserver: available
```

## Slice 1 - RW-heavy scenario contract

Status: implemented.

Files:

- `datawraith/core/types.py`
- `datawraith/engine/scenarios/rw_heavy.py`
- `datawraith/engine/scenarios/__init__.py`
- `tests/test_rw_heavy.py`
- `tests/test_scenario_contract.py`

Public CLI:

```bash
sdb attack rw-heavy --dry-run --row-count 10 --operations 20
```

## Slice 2 - Workload MVP

Status: implemented behind `--execute`.

Behavior:

- Starts local embedded ShadowDB through the existing CLI execution path.
- Creates local `dw_customers`, `dw_products`, and `dw_orders` tables if missing.
- Seeds deterministic product/customer/order-style rows.
- Runs mixed SELECT/INSERT/UPDATE asyncpg workers.
- Supports `--read-ratio`, `--row-count`, `--operations`, `--workers`, and `--duration`.

Acceptance after Python 3.12 + `pgserver` is available:

```bash
sdb attack rw-heavy --execute --duration 10 --workers 2 --row-count 10 --operations 20 --output rw-heavy.json
python -m json.tool rw-heavy.json
```

## Slice 3 - Rule-based analyzer

Status: implemented.

Files:

- `datawraith/engine/analyzer.py`
- `tests/test_analyzer.py`

Behavior:

- Aggregates slow query samples into `ScenarioResult.top_culprits`.
- Emits safe hints for join-heavy reads, time-window filters, GROUP BY scans, and primary-key update paths.
- Does not run EXPLAIN yet; EXPLAIN collection is future work after real DB verification.

## Slice 4 - Compare command

Status: implemented.

Files:

- `datawraith/output/comparator.py`
- `datawraith/cli.py`
- `tests/test_output.py`
- `tests/test_cli.py`

Public CLI:

```bash
sdb compare baseline.json current.json
```

Compared metrics:

- health score
- average/max QPS
- p95/p99 latency
- error rate

## Slice 5 - Executable workflow

Status: implemented as a secondary distribution path.

Files:

- `DataWraith.spec`
- `.github/workflows/executable.yml`

Build command:

```bash
pyinstaller DataWraith.spec --clean --noconfirm
dist/sdb.exe --version
```

Primary distribution remains `pip install datawraith`.

## Verification commands

Always run:

```bash
ruff check .
mypy datawraith
pytest
python -m build
mkdocs build --strict
sdb attack rw-heavy --dry-run --row-count 10 --operations 20
```

Run only on Python 3.12 with `pgserver` available:

```bash
sdb attack rw-heavy --execute --duration 10 --workers 2 --row-count 10 --operations 20 --output rw-heavy.json
sdb compare rw-heavy.json rw-heavy.json
python -m json.tool rw-heavy.json
```

## Remaining work after this slice

- Real Python 3.12 + `pgserver` E2E verification for Phase 1 and Phase 2.
- Optional `sdb attack --all --execute --output-dir reports/`.
- Interactive TUI screen for RW-heavy configuration and report summary.
- EXPLAIN-based analyzer once query collection is proven safe and fast.
