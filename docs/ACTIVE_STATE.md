# DataWraith ? Active State

Last updated: 2026-05-30

## Current Status

DataWraith v1 MVP code paths exist for local PostgreSQL chaos/security testing:
Concurrency, R/W-heavy, Migration Lock, Security/Isolation, JSON/SARIF/JUnit/PDF
reports, CLI quickstart/recipes, local PostgreSQL fallback, and the market-product demo.

The project memory system is consolidated to three files under `docs/`:
`ProjectBrief.md`, `Architecture.md`, and this `ACTIVE_STATE.md`.

## Priority Backlog

### P0 ? Runtime E2E verification

- [ ] Run local PostgreSQL fallback E2E with Docker or a configured localhost DB.
- [ ] Run `examples/market-product-demo/run-demo.ps1` end-to-end.
- [ ] Verify generated demo reports: JSON, SARIF, JUnit XML, and PDF.
- [ ] Run Python 3.12 embedded `pgserver` E2E before any release tag.

### P1 ? CI and release readiness

- [ ] Confirm latest GitHub Actions PostgreSQL fallback E2E is green on the active release PR/branch.
- [ ] Run standard local gates: `ruff check .`, `mypy datawraith`, `pytest`, `python -m build`, `mkdocs build --strict`.
- [ ] Prepare release notes/checklist after real E2E passes.

### P2 ? TUI UX hardening

- [ ] Expand the Textual dashboard from command hints into interactive forms/buttons for init, seed, attack, compare, and report flows.
- [ ] Add screenshots/GIFs only after the TUI is interactive enough to showcase.

### P3 ? Future design backlog

- [ ] Design an explicit remote-shadow mode for disposable Neon/Supabase branches only if strong safeguards are specified.
- [ ] Keep v1 default local-only and continue rejecting non-local PostgreSQL URLs.
- [ ] Keep provider-backed AI/network enrichment deferred until a safe BYOK execution policy is designed.

## Validation Gaps

- Local environment recently used Python 3.13 without embedded `pgserver`; execute flows need Docker/local PostgreSQL fallback or Python 3.12.
- The market-product demo schema and sample data parsed in dry-run, but full execute demo still needs a running local PostgreSQL runtime.
- Windows embedded `pgserver` is flaky on GitHub runners; real DB coverage should rely on Linux/macOS embedded jobs and the PostgreSQL fallback E2E job.

## Active Risks / Constraints

- Never target production or non-local databases with chaos/security scenarios.
- Cloud PostgreSQL providers such as Neon/Supabase are PostgreSQL-compatible, but v1 must use schema-only export into a local shadow DB.
- `pgserver` 0.1.4 does not support Python 3.13 embedded startup; Python 3.13 users should use `DATAWRAITH_DATABASE_URL` with localhost PostgreSQL.
- AI advice remains offline-first and human-reviewed; no provider-backed network calls or auto-applied SQL until a safer policy exists.

## Next Execution Gate

Before feature work, choose one:

```text
[AUTO] Start the P0 local PostgreSQL fallback E2E + market-product demo verification.
[EDIT] Re-prioritize this backlog first.
```
