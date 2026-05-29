# DataWraith - Active State

Last updated: 2026-05-30

## Current Status

DataWraith v1 MVP code paths exist for local PostgreSQL chaos/security testing:
Concurrency, R/W-heavy, Migration Lock, Security/Isolation, JSON/SARIF/JUnit/PDF
reports, CLI quickstart/recipes, local PostgreSQL fallback, and the market-product demo.

The project memory system is consolidated to three files under `docs/`:
`ProjectBrief.md`, `Architecture.md`, and this `ACTIVE_STATE.md`.

## Latest Work

- P0 local PostgreSQL fallback verification was attempted on this machine.
- Docker CLI is not installed, so the bundled Docker fallback could not be started here.
- A PostgreSQL server is listening on localhost:5432, but the documented demo URL
  `postgresql://datawraith:datawraith@localhost:5432/datawraith` fails authentication.
- `sdb doctor --json` now validates configured local PostgreSQL fallback connectivity instead of reporting a configured but unusable URL as healthy.
- `examples/market-product-demo/run-demo.ps1` now fails fast on `sdb` command errors and rejects durations below DataWraith's 10-second scenario minimum.

## Priority Backlog

### P0 - Runtime E2E verification

- [ ] Start or configure a known-good local PostgreSQL database for DataWraith E2E.
  - Preferred: install/start Docker and run `docker compose up -d postgres`.
  - Alternative: provide a working localhost PostgreSQL URL in `DATAWRAITH_DATABASE_URL`.
- [ ] Run `examples/market-product-demo/run-demo.ps1` end-to-end.
- [ ] Verify generated demo reports: JSON, SARIF, JUnit XML, and PDF.
- [ ] Run Python 3.12 embedded `pgserver` E2E before any release tag.

### P1 - CI and release readiness

- [ ] Confirm latest GitHub Actions PostgreSQL fallback E2E is green on the active release PR/branch.
- [x] Run standard local gates available on this machine: `ruff check`, `mypy datawraith`, `pytest`, `python -m build`, `mkdocs build --strict`.
- [ ] Prepare release notes/checklist after real E2E passes.

### P2 - TUI UX hardening

- [ ] Expand the Textual dashboard from command hints into interactive forms/buttons for init, seed, attack, compare, and report flows.
- [ ] Add screenshots/GIFs only after the TUI is interactive enough to showcase.

### P3 - Future design backlog

- [ ] Design an explicit remote-shadow mode for disposable Neon/Supabase branches only if strong safeguards are specified.
- [ ] Keep v1 default local-only and continue rejecting non-local PostgreSQL URLs.
- [ ] Keep provider-backed AI/network enrichment deferred until a safe BYOK execution policy is designed.

## Validation Log

- `docker --version`: failed, Docker CLI not installed.
- `Test-NetConnection localhost -Port 5432`: succeeded, but credentials for the documented demo URL failed.
- `sdb doctor --json` with documented demo URL: correctly reports `database_url.ok=false` due authentication failure.
- `powershell -ExecutionPolicy Bypass -File examples/market-product-demo/run-demo.ps1 -Duration 10 ...`: blocked at schema load because local PostgreSQL authentication failed.
- `pytest tests/test_cli.py`: passed, 31 tests.
- `ruff check datawraith/cli.py tests/test_cli.py`: passed.
- `mypy datawraith`: passed.
- `pytest`: passed, 75 passed / 11 skipped.
- `python -m build`: passed.
- `mkdocs build --strict`: passed with existing informational source-blueprint anchor messages.

## Active Risks / Constraints

- Never target production or non-local databases with chaos/security scenarios.
- Cloud PostgreSQL providers such as Neon/Supabase are PostgreSQL-compatible, but v1 must use schema-only export into a local shadow DB.
- `pgserver` 0.1.4 does not support Python 3.13 embedded startup; Python 3.13 users should use `DATAWRAITH_DATABASE_URL` with localhost PostgreSQL.
- AI advice remains offline-first and human-reviewed; no provider-backed network calls or auto-applied SQL until a safer policy exists.

## Next Execution Gate

```text
[AUTO] Continue P0 by installing/starting a known-good local PostgreSQL runtime, then rerun the market-product demo E2E.
[EDIT] Re-prioritize this backlog first.
```
