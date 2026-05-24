# DataWraith - Phase 3 Build Plan

Phase 3 adds the Migration Lock scenario and an offline-first BYOK AI advisory
surface. It remains local-only: all DDL execution goes through embedded
ShadowDB, and AI suggestions are advisory only and never auto-applied.

## Current target

```bash
sdb attack migration --execute --duration 10 --workers 2 --row-count 10 --operations 20 --output migration.json
sdb ai analyze migration.json --provider openai
sdb ai analyze migration.json --json
```

## Runtime gate

Migration execution uses the same embedded PostgreSQL dependency as earlier
phases. On Python 3.13 without `pgserver`, real DB E2E tests are skipped.

Required environment for real E2E:

```bash
python --version  # Python 3.12.x
sdb doctor        # pgserver: available
```

## Slice 1 - Migration config and scenario

Status: implemented in code and covered by fake-DB/unit tests. Real DB E2E is
pgserver-gated.

Files:

- `datawraith/core/types.py`
- `datawraith/engine/scenarios/migration.py`
- `datawraith/engine/scenarios/__init__.py`
- `tests/test_migration.py`
- `tests/test_phase3_e2e.py`

Behavior:

- Prepares a local `dw_migration_items` table by default.
- Runs SELECT/UPDATE background workload.
- Executes allowlisted DDL operations:
  - `ALTER TABLE ... ADD COLUMN IF NOT EXISTS ...`
  - `CREATE INDEX IF NOT EXISTS ...`
- Applies session `lock_timeout` and `statement_timeout`.
- Tracks QPS, latency, errors, lock timeout count, and lock-wait estimate.

## Slice 2 - Rule-based migration analyzer

Status: implemented.

Files:

- `datawraith/engine/migration_analysis.py`
- `tests/test_migration_analysis.py`

Behavior:

- Converts lock pressure and long migration duration into `top_culprits`.
- Produces deterministic `AISuggestion` advisory records for:
  - safer add-column rollout
  - concurrent index advice
  - lock/statement timeout advice

## Slice 3 - AI BYOK bridge

Status: implemented as offline-first advisory bridge. No network calls are made
in this slice.

Files:

- `datawraith/ai/advisor.py`
- `datawraith/cli.py`
- `tests/test_cli.py`

Public CLI:

```bash
sdb ai setup --provider openai --api-key <key>
sdb ai status --provider openai
sdb ai analyze migration.json --provider openai
sdb ai analyze migration.json --json
```

Rules:

- Keys are stored through OS keyring.
- No DataWraith-shipped keys.
- No telemetry.
- No auto-applied SQL fixes.
- Provider-backed network enrichment is intentionally deferred until the local
  rule-based contract is stable.

## Verification commands

Always run:

```bash
ruff check .
mypy datawraith
pytest
python -m build
mkdocs build --strict
sdb attack migration --dry-run --row-count 10 --operations 20
```

Run only on Python 3.12 with `pgserver` available:

```bash
sdb attack migration --execute --duration 10 --workers 2 --row-count 10 --operations 20 --output migration.json
sdb ai analyze migration.json --provider openai
sdb ai analyze migration.json --json
python -m json.tool migration.json
```

## Remaining work after this slice

- Real Python 3.12 + `pgserver` E2E verification for migration scenario.
- Provider-backed single-call AI enrichment with explicit user-provided keys.
- Interactive TUI screen for migration configuration and AI suggestion display.
- More migration operation templates after safety review.
