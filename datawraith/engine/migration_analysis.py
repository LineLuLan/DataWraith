"""Rule-based migration risk analysis for Phase 3."""

from __future__ import annotations

from dataclasses import dataclass

from datawraith.core.types import AISuggestion, Culprit, ScenarioResult, ScenarioType


@dataclass(frozen=True)
class MigrationObservation:
    """Observed migration behavior used by the rule-based analyzer."""

    operation: str
    lock_timeout_ms: int
    migration_duration_ms: float
    blocked_operations: int
    error_count: int


def culprits_for_migration(observation: MigrationObservation) -> list[Culprit]:
    """Convert migration observations into stable ScenarioResult culprits."""
    culprits: list[Culprit] = []
    if observation.blocked_operations > 0:
        culprits.append(
            Culprit(
                rank=1,
                query_text=observation.operation,
                impact_pct=60.0,
                calls=observation.blocked_operations,
                mean_exec_time_ms=observation.migration_duration_ms,
                execution_plan=(
                    "Migration overlapped with active workload and observed blocked or timed-out "
                    "operations. Prefer lock_timeout, short transactions, and off-peak rollout."
                ),
            )
        )
    if observation.migration_duration_ms > observation.lock_timeout_ms:
        culprits.append(
            Culprit(
                rank=len(culprits) + 1,
                query_text=observation.operation,
                impact_pct=40.0,
                calls=1,
                mean_exec_time_ms=observation.migration_duration_ms,
                execution_plan=(
                    "Migration duration exceeded configured lock_timeout. Split heavyweight DDL "
                    "or use non-blocking alternatives where PostgreSQL supports them."
                ),
            )
        )
    return culprits


def migration_suggestions_for_result(result: ScenarioResult) -> list[AISuggestion]:
    """Return deterministic advisory suggestions for migration reports.

    The return type uses the Phase 3 `AISuggestion` contract, but these
    suggestions are rule-based and offline. Provider-backed AI can later enrich
    this output without changing the CLI contract.
    """
    if result.scenario_type != ScenarioType.MIGRATION:
        return [
            AISuggestion(
                provider="rules",
                model="datawraith-local-rules",
                reasoning="Report is not a migration scenario; no migration-specific advice.",
                risk_level="low",
            )
        ]

    suggestions: list[AISuggestion] = []
    config = result.config
    operation = str(config.get("migration_operation", "migration"))
    lock_timeout_ms = int(config.get("lock_timeout_ms", 0) or 0)

    if operation == "create_index":
        suggestions.append(
            AISuggestion(
                provider="rules",
                model="datawraith-local-rules",
                reasoning=(
                    "CREATE INDEX can block writes. For production PostgreSQL, consider "
                    "CREATE INDEX CONCURRENTLY after validating it is safe for your migration tool."
                ),
                sql_fix="CREATE INDEX CONCURRENTLY IF NOT EXISTS ...",
                risk_level="medium",
                rollback_plan="DROP INDEX CONCURRENTLY IF EXISTS <index_name>;",
            )
        )
    if operation == "add_column":
        suggestions.append(
            AISuggestion(
                provider="rules",
                model="datawraith-local-rules",
                reasoning=(
                    "Adding nullable columns is usually safer than adding NOT NULL columns with "
                    "defaults. Backfill separately in batches before adding constraints."
                ),
                sql_fix="ALTER TABLE <table> ADD COLUMN IF NOT EXISTS <column> boolean;",
                risk_level="low",
                rollback_plan="ALTER TABLE <table> DROP COLUMN IF EXISTS <column>;",
            )
        )
    if result.metrics.error_count > 0 or result.metrics.lock_wait_ms_total > 0:
        suggestions.append(
            AISuggestion(
                provider="rules",
                model="datawraith-local-rules",
                reasoning=(
                    "The run observed errors or lock wait time. Add lock_timeout and "
                    "statement_timeout to migration sessions and retry during low traffic."
                ),
                sql_fix=f"SET lock_timeout = '{max(lock_timeout_ms, 500)}ms';",
                risk_level="medium",
                rollback_plan="Reset session timeouts after the migration transaction.",
            )
        )
    if not suggestions:
        suggestions.append(
            AISuggestion(
                provider="rules",
                model="datawraith-local-rules",
                reasoning="No high-risk migration pattern detected in this local report.",
                risk_level="low",
            )
        )
    return suggestions
