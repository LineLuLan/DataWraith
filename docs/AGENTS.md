# DataWraith Agent Instructions

## Source of truth

Read these before significant changes. All Markdown documentation lives in
`docs/`, so paths below are relative to the repository root:

1. `docs/ProjectBrief.md`
2. `docs/Architecture.md`
3. `docs/BuildPlan_Phase1.md`
4. `docs/Roadmap.md`
5. `docs/Tracker.md`
6. `docs/Handoff.md`
7. `docs/Decisions.md`
8. `docs/DataWraith_Brief.md`
9. `docs/DataWraith_Blueprint_E2E.md`

## Engineering rules

- Python 3.12+ code style, typed, async-first for I/O.
- Do not connect to production databases.
- Keep Phase 1 focused on the engine foundation and Concurrency Test.
- AI, standalone `.exe`, SARIF/JUnit/PDF, and non-PostgreSQL databases are future phases.
- Run the narrowest relevant validation before reporting completion.
