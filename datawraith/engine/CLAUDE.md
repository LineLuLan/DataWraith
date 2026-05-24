# Engine Module — Dev A Domain

## Responsibility

Owns scenario execution, seeding, analysis, and `ShadowDB` integration.

## Contracts

Every scenario implements:

- `name: str`
- `display_name: str`
- `validate_config() -> list[str]`
- `async run() -> AsyncIterator[ScenarioEvent]`

The final event must be `EventType.COMPLETED` when the scenario completes.

## Phase 1 priority

Replace the scaffold `ConcurrencyScenario` with a real asyncpg workload that
detects deadlocks, lock waits, MVCC bloat, and rollback rate.
