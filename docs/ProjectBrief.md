# DataWraith — Project Brief

DataWraith is a local PostgreSQL chaos-testing tool for developers who need to
stress-test database behavior before production incidents happen.

## Positioning

- One-liner: `pip install datawraith` then `sdb` to chaos-test PostgreSQL locally.
- Primary distribution: Python package.
- Terminal alias: `sdb`.
- License: MIT.
- Product philosophy: engine-first; AI is opt-in and deferred.

## Phase 1 outcome

Ship a reliable foundation for the Concurrency Test scenario:

- installable package
- CLI/TUI entrypoint
- embedded shadow DB abstraction
- scenario contracts
- JSON result export
- CI-backed quality gates

## Explicitly deferred

- AI BYOK analysis until Phase 3
- standalone `.exe` until Phase 2
- SARIF/JUnit/PDF until Phase 4
- hosted services, telemetry, and non-PostgreSQL databases
