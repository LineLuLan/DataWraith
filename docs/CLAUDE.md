# DataWraith — Claude Code Context

## Project

DataWraith is a PostgreSQL chaos-testing tool. It is pip-installable, runs
local-first, uses embedded PostgreSQL through `pgserver`, and is MIT licensed.

## Stack lock-in

- Python 3.12 baseline
- Typer CLI with `sdb` and `datawraith` entrypoints
- Textual TUI
- Pydantic 2 contracts
- psycopg 3 + asyncpg for PostgreSQL access
- pgserver for embedded PostgreSQL where wheels are available

## Current scaffold status

This repo contains the first scaffold: package metadata, public contracts,
import-safe modules, minimal TUI, JSON output, CI, tests, and project memory docs.
All Markdown documentation is centralized under `docs/`.

## Hard rules

- No production DB writes.
- No telemetry or external service calls by default.
- No `print()` in library internals; CLI may use Typer output.
- Keep module API contracts stable unless `docs/Architecture.md` and, when active state changes, `docs/ACTIVE_STATE.md` are updated.
- Prefer root-cause fixes and focused tests.

## Module ownership

- Dev A: `datawraith/engine/`, `datawraith/core/shadow_db.py`
- Dev B: `datawraith/tui/`, `datawraith/output/`
- Dev C: packaging, CI, `datawraith/ai/` from Phase 3 onward
