# DataWraith

DataWraith is a local PostgreSQL chaos-testing tool. Phase 1 focuses on the
Concurrency Test foundation.

## Start here for new sessions

Read these in order:

1. `ProjectBrief.md` — product source of truth summary.
2. `Architecture.md` — current scaffold contracts and boundaries.
3. `BuildPlan_AllPhases.md` — cross-phase build roadmap.
4. `BuildPlan_Phase1.md` — detailed current phase build roadmap.
5. `Tracker.md` — current completed/next state.
6. `Handoff.md` — latest implementation notes and known limits.
7. `Decisions.md` — tradeoffs already chosen.

The original source documents are preserved in:

- `DataWraith_Brief.md`
- `DataWraith_Blueprint_E2E.md`

## Documentation layout rule

All Markdown documentation lives in `docs/`. `pyproject.toml` reads the package
README from `docs/PackageREADME.md`, and MkDocs navigation links to the project
memory files from this folder.
