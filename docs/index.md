# DataWraith

DataWraith is a local PostgreSQL chaos-testing tool. Phase 1 focuses on the
Concurrency Test foundation, and Phase 2 adds the first RW-heavy workload behind
the same embedded PostgreSQL runtime gate.

## Start here for new sessions

Read these in order:

1. `ProjectBrief.md` - product source of truth summary.
2. `Architecture.md` - current scaffold contracts and boundaries.
3. `BuildPlan_AllPhases.md` - cross-phase build roadmap.
4. `BuildPlan_Phase1.md` - detailed Phase 1 build roadmap.
5. `BuildPlan_Phase2.md` - detailed Phase 2 build roadmap.
6. `BuildPlan_Phase3.md` - detailed Phase 3 build roadmap.
7. `Tracker.md` - current completed/next state.
8. `Handoff.md` - latest implementation notes and known limits.
9. `Decisions.md` - tradeoffs already chosen.

The original source documents are preserved in:

- `DataWraith_Brief.md`
- `DataWraith_Blueprint_E2E.md`

## Documentation layout rule

All Markdown documentation lives in `docs/`. `pyproject.toml` reads the package
README from `docs/PackageREADME.md`, and MkDocs navigation links to the project
memory files from this folder.
