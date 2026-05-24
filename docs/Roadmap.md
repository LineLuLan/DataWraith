# DataWraith — Roadmap

## Phase 1 — v0.1 Concurrency foundation

- Package scaffold and CI
- Shadow DB wrapper
- Scenario contracts and registry
- Concurrency Test implementation
- Textual live log and metrics UI
- JSON export
- Gate: Python 3.12 + `pgserver` real DB verification before alpha release

## Phase 2 — v0.2 R/W Heavy + executable

- Read/write heavy scenario
- Headless attack mode
- Compare runs
- PyInstaller build
- Rule-based slow-query/full-scan analysis
- Conservative laptop-safe defaults
- Gate: real embedded PostgreSQL verification still requires Python 3.12 +
  `pgserver`; Python 3.13 validates unit/dry-run paths only.

## Phase 3 — v0.3 Migration Lock + AI BYOK

- Migration lock scenario
- User-provided AI keys through secure local storage
- Single-call AI suggestions, never auto-applied
- Rule-based migration suggestions before AI suggestions

## Phase 4 — v1.0 Security & Isolation

- RLS/multi-tenant leak checks
- SQL injection fuzzing
- SARIF/JUnit/PDF reports
- v1.0 launch readiness

## Detailed plan

See `docs/BuildPlan_AllPhases.md`, `docs/BuildPlan_Phase2.md`,
`docs/BuildPlan_Phase3.md`, and `docs/BuildPlan_Phase4.md` for file-level
execution order, acceptance commands, and cross-phase constraints.
