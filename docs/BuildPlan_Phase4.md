# DataWraith - Phase 4 Build Plan

Phase 4 adds the practical v1.0 security/isolation scenario and CI-friendly
report exporters. Execution remains local-only through embedded ShadowDB; no
external or production database support is introduced.

## Current target

```bash
sdb attack security --execute --duration 10 --tenants 2 --rows-per-tenant 2 --output security.json
sdb report security.json --format sarif --output security.sarif
sdb report security.json --format junit --output security.xml
sdb report security.json --format pdf --output security.pdf
```

## Runtime gate

Security execution uses the same embedded PostgreSQL dependency as earlier
phases. On Python 3.13 without `pgserver`, real DB E2E tests are skipped.

Required environment for real E2E:

```bash
python --version  # Python 3.12.x
sdb doctor        # pgserver: available
```

## Slice 1 - Security scenario

Status: implemented in code and covered by fake-DB/unit tests. Real DB E2E is
pgserver-gated.

Behavior:

- Prepares local tenants, users, and records fixtures.
- Enables and forces row-level security on the local records table.
- Checks tenant-scoped access using `datawraith.tenant_id` session context.
- Runs safe SQL injection fuzz payloads through parameterized queries.
- Checks basic privilege posture where embedded PostgreSQL supports it.
- Emits `ScenarioResult` with security findings as culprits/raw logs.

Public CLI:

```bash
sdb attack security --dry-run
sdb attack security --execute --duration 10 --output security.json
sdb attack --all --execute --output-dir reports/
```

## Slice 2 - Security analysis helpers

Status: implemented.

Behavior:

- Converts failed security checks into `Culprit` records.
- Calculates conservative security health score from failed findings and errors.
- Includes deterministic SQL injection fuzz payloads, all executed as parameters.

## Slice 3 - Multi-format reports

Status: implemented.

Public CLI:

```bash
sdb report security.json --format sarif --output security.sarif
sdb report security.json --format junit --output security.xml
sdb report security.json --format pdf --output security.pdf
```

Behavior:

- SARIF v2.1.0 for GitHub Security-compatible ingestion.
- JUnit XML for CI test result surfaces.
- Minimal valid PDF generated without heavy dependencies.

## Verification commands

Always run:

```bash
ruff check .
mypy datawraith
pytest
python -m build
mkdocs build --strict
sdb attack security --dry-run
```

Run only on Python 3.12 with `pgserver` available:

```bash
sdb attack security --execute --duration 10 --tenants 2 --rows-per-tenant 2 --output security.json
sdb report security.json --format sarif --output security.sarif
sdb report security.json --format junit --output security.xml
sdb report security.json --format pdf --output security.pdf
python -m json.tool security.json
```

## Remaining work after this slice

- Real Python 3.12 + `pgserver` E2E verification for security scenario and reports.
- Polished PDF/report design after schema stabilizes.
- Interactive TUI screen for security configuration and report export.
- Release changelog/demo assets after all stacked PRs merge.
