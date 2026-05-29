# DataWraith Agent Instructions

## Source of truth

Read these before significant changes. Markdown documentation lives in `docs/`;
the only root Markdown exception is `README.md` for the GitHub landing page.
Paths below are relative to the repository root:

1. `docs/ProjectBrief.md`
2. `docs/Architecture.md`
3. `docs/ACTIVE_STATE.md`
4. `docs/BuildPlan_Phase1.md`
5. `docs/DataWraith_Brief.md`
6. `docs/DataWraith_Blueprint_E2E.md`

## Engineering rules

- Python 3.12+ code style, typed, async-first for I/O.
- Do not connect to production databases.
- Keep new work aligned with the local-only PostgreSQL safety model.
- Phase 1-4 MVP code paths now exist; future work should harden E2E
  verification, launch docs, and UX before expanding scope.
- AI provider calls, publishing standalone `.exe` artifacts, hosted services,
  telemetry, and non-PostgreSQL databases remain future work unless explicitly
  scoped.
- Run the narrowest relevant validation before reporting completion.
