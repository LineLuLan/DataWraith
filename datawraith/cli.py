"""Typer CLI entry point for DataWraith."""

from __future__ import annotations

import asyncio
import importlib.util
import json
import sys
from pathlib import Path
from typing import Annotated, cast

import psycopg
import typer

from datawraith import __version__
from datawraith.ai.advisor import analyze_report, has_api_key, store_api_key
from datawraith.core.config import get_settings
from datawraith.core.database_url import validate_local_database_url
from datawraith.core.exceptions import DataWraithError
from datawraith.core.shadow_db import ShadowDB
from datawraith.core.types import (
    ConcurrencyConfig,
    EventType,
    MigrationConfig,
    RWHeavyConfig,
    ScenarioConfig,
    ScenarioResult,
    SecurityConfig,
)
from datawraith.engine.runner import run_scenario
from datawraith.engine.schema_parser import parse_schema
from datawraith.engine.seeder import (
    SeedPlan,
    execute_seed_plan,
    parse_column_specs,
    render_insert_sql,
)
from datawraith.output.ascii_renderer import render_result
from datawraith.output.comparator import compare_results, load_result, render_comparison
from datawraith.output.json_exporter import JSONExporter
from datawraith.output.report_exporter import ReportFormat, export_report

app = typer.Typer(
    name="sdb",
    help="DataWraith PostgreSQL chaos-testing CLI.",
    invoke_without_command=True,
    no_args_is_help=False,
    pretty_exceptions_show_locals=False,
    rich_markup_mode="rich",
)
ai_app = typer.Typer(
    name="ai",
    help="Optional BYOK advisory commands. Offline rules are always available.",
    rich_markup_mode="rich",
)
app.add_typer(ai_app, name="ai")

QUICKSTART_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS dw_quickstart_products (
    id integer,
    name text NOT NULL,
    stock integer NOT NULL DEFAULT 0
);
"""
QUICKSTART_TABLE = "dw_quickstart_products"


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"DataWraith {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=_version_callback,
            is_eager=True,
            help="Show DataWraith version and exit.",
        ),
    ] = False,
) -> None:
    """Open the TUI when no subcommand is provided."""
    _ = version
    if ctx.invoked_subcommand is None:
        from datawraith.tui.app import run

        run()


@app.command()
def doctor(
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Emit machine-readable JSON health check output."),
    ] = False,
) -> None:
    """Check local runtime readiness."""
    checks = _collect_doctor_checks()
    if json_output:
        typer.echo(
            json.dumps(
                {
                    "checks": [
                        {"name": name, "ok": ok, "detail": detail}
                        for name, ok, detail in checks
                    ],
                    "ok": all(ok for _, ok, _ in checks),
                },
                indent=2,
            )
        )
        return

    for name, ok, detail in checks:
        icon = "OK" if ok else "WARN"
        typer.echo(f"[{icon}] {name}: {detail}")


@app.command()
def recipes() -> None:
    """Print copy-pasteable commands so users do not need to memorize syntax."""
    typer.echo("DataWraith recipes")
    typer.echo("")
    typer.echo("1) Check runtime")
    typer.echo("   sdb doctor")
    typer.echo("")
    typer.echo("2) Fast dry-run tour")
    typer.echo("   sdb quickstart")
    typer.echo("")
    typer.echo("3) Local PostgreSQL fallback")
    typer.echo("   docker compose up -d postgres")
    typer.echo(
        "   $env:DATAWRAITH_DATABASE_URL="
        '"postgresql://datawraith:datawraith@localhost:5432/datawraith"'
    )
    typer.echo("")
    typer.echo("4) Run v1 smoke flow")
    typer.echo("   sdb quickstart --execute --output-dir reports")
    typer.echo("")
    typer.echo("5) Individual attacks")
    typer.echo("   sdb attack concurrency --dry-run")
    typer.echo("   sdb attack rw-heavy --dry-run --row-count 10 --operations 20")
    typer.echo("   sdb attack migration --dry-run")
    typer.echo("   sdb attack security --dry-run")
    typer.echo("")
    typer.echo("6) Reports")
    typer.echo("   sdb compare reports/concurrency.json reports/rw-heavy.json")
    typer.echo("   sdb report reports/security.json --format sarif --output reports/security.sarif")


@app.command()
def quickstart(
    execute: Annotated[
        bool,
        typer.Option("--execute", help="Run the local v1 smoke flow instead of printing commands."),
    ] = False,
    output_dir: Annotated[
        Path,
        typer.Option("--output-dir", help="Directory for generated quickstart reports."),
    ] = Path("reports"),
    duration: Annotated[int, typer.Option("--duration", help="Scenario duration in seconds.")] = 10,
    workers: Annotated[int, typer.Option("--workers", help="Concurrent worker count.")] = 2,
    rows: Annotated[int, typer.Option("--rows", help="Seed rows for quickstart products.")] = 10,
    operations: Annotated[
        int,
        typer.Option("--operations", help="Operation cap for workload scenarios."),
    ] = 20,
    data_dir: Annotated[
        Path | None,
        typer.Option("--data-dir", help="ShadowDB data directory. Defaults to .datawraith/shadow."),
    ] = None,
    database_url: Annotated[
        str | None,
        typer.Option(
            "--database-url",
            help=(
                "Use a local PostgreSQL URL instead of embedded pgserver. "
                "Defaults to DATAWRAITH_DATABASE_URL when set."
            ),
        ),
    ] = None,
) -> None:
    """Guided v1 smoke flow with safe laptop defaults."""
    if not execute:
        typer.echo("Quickstart dry-run. Copy one of these:")
        typer.echo("")
        typer.echo("  sdb doctor")
        typer.echo("  sdb recipes")
        typer.echo("  sdb quickstart --execute --output-dir reports")
        typer.echo("")
        typer.echo("If Python 3.13+ or pgserver is unavailable:")
        typer.echo("  docker compose up -d postgres")
        typer.echo(
            "  $env:DATAWRAITH_DATABASE_URL="
            '"postgresql://datawraith:datawraith@localhost:5432/datawraith"'
        )
        typer.echo("  sdb quickstart --execute --output-dir reports")
        return

    try:
        reports = _run_quickstart(
            output_dir=output_dir,
            duration=duration,
            workers=workers,
            rows=rows,
            operations=operations,
            data_dir=data_dir or get_settings().shadow_data_dir,
            database_url=database_url,
        )
    except DataWraithError as exc:
        typer.echo(f"Quickstart failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo("Quickstart complete.")
    for report_path in reports:
        typer.echo(f"- {report_path}")
    typer.echo("")
    typer.echo(f"Next: sdb compare {output_dir / 'concurrency.json'} {output_dir / 'rw-heavy.json'}")
    typer.echo(
        "Next: "
        f"sdb report {output_dir / 'security.json'} --format sarif "
        f"--output {output_dir / 'security.sarif'}"
    )


@app.command()
def init(
    schema_path: Annotated[Path, typer.Argument(help="Path to a PostgreSQL schema.sql file.")],
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Parse and summarize without starting embedded PostgreSQL."),
    ] = True,
    execute: Annotated[
        bool,
        typer.Option("--execute", help="Load schema into the local embedded ShadowDB."),
    ] = False,
    data_dir: Annotated[
        Path | None,
        typer.Option("--data-dir", help="ShadowDB data directory. Defaults to .datawraith/shadow."),
    ] = None,
    database_url: Annotated[
        str | None,
        typer.Option(
            "--database-url",
            help=(
                "Use a local PostgreSQL URL instead of embedded pgserver. "
                "Defaults to DATAWRAITH_DATABASE_URL when set."
            ),
        ),
    ] = None,
) -> None:
    """Parse a schema file and prepare a future shadow DB init flow."""
    if not schema_path.exists():
        raise typer.BadParameter(f"Schema file does not exist: {schema_path}")
    schema_sql = schema_path.read_text(encoding="utf-8")
    try:
        summary = parse_schema(schema_sql)
    except DataWraithError as exc:
        typer.echo(f"Schema error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Schema statements: {summary.statement_count}")
    typer.echo(f"Tables discovered: {len(summary.tables)}")
    for table in summary.tables:
        typer.echo(f"- {table.name}")
    for warning in summary.warnings:
        typer.echo(f"[WARN] {warning}")

    if execute:
        target_data_dir = data_dir or get_settings().shadow_data_dir
        db: ShadowDB | None = None
        try:
            db = _create_shadow_db(target_data_dir, database_url)
            db.start()
            # Execute the original schema, not comment-stripped statements, so
            # PostgreSQL remains the source of truth for valid DDL syntax.
            asyncio.run(db.load_schema(schema_sql))
            loaded_tables = db.list_tables()
        except DataWraithError as exc:
            typer.echo(f"ShadowDB init failed: {exc}", err=True)
            raise typer.Exit(code=1) from exc
        finally:
            if db is not None:
                db.stop()

        typer.echo(f"ShadowDB data dir: {target_data_dir}")
        typer.echo(f"Loaded tables: {len(loaded_tables)}")
        for table_name in loaded_tables:
            typer.echo(f"* {table_name}")
        return

    if dry_run:
        typer.echo("Dry-run only; pass --execute to load this schema into local ShadowDB.")


@app.command()
def seed(
    table: Annotated[str, typer.Option("--table", help="Target table name.")],
    columns: Annotated[
        list[str],
        typer.Option("--column", "-c", help="Column spec in name:kind form. Repeatable."),
    ],
    rows: Annotated[int, typer.Option("--rows", help="Number of rows to plan.")] = 10,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Render a deterministic SQL preview only."),
    ] = True,
    execute: Annotated[
        bool,
        typer.Option("--execute", help="Insert generated rows into the local embedded ShadowDB."),
    ] = False,
    data_dir: Annotated[
        Path | None,
        typer.Option("--data-dir", help="ShadowDB data directory. Defaults to .datawraith/shadow."),
    ] = None,
    database_url: Annotated[
        str | None,
        typer.Option(
            "--database-url",
            help=(
                "Use a local PostgreSQL URL instead of embedded pgserver. "
                "Defaults to DATAWRAITH_DATABASE_URL when set."
            ),
        ),
    ] = None,
) -> None:
    """Create a deterministic seed plan preview."""
    try:
        plan = SeedPlan(table=table, rows=rows, columns=parse_column_specs(columns))
    except DataWraithError as exc:
        typer.echo(f"Seeder error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    if execute:
        target_data_dir = data_dir or get_settings().shadow_data_dir
        db: ShadowDB | None = None
        try:
            db = _create_shadow_db(target_data_dir, database_url)
            db.start()
            result = execute_seed_plan(db, plan)
        except DataWraithError as exc:
            typer.echo(f"Seeder execution failed: {exc}", err=True)
            raise typer.Exit(code=1) from exc
        finally:
            if db is not None:
                db.stop()

        typer.echo(
            f"Inserted {result.rows_inserted}/{result.rows_requested} rows "
            f"into {result.table} in {result.duration_seconds:.2f}s"
        )
        return

    typer.echo(render_insert_sql(plan))
    if dry_run:
        typer.echo("Dry-run only; pass --execute to insert into local ShadowDB.")


@app.command()
def attack(
    scenario: Annotated[
        str | None,
        typer.Argument(help="Scenario name. Supports concurrency, rw-heavy, migration, and security."),
    ] = None,
    duration: Annotated[int, typer.Option("--duration", help="Duration in seconds.")] = 10,
    workers: Annotated[int, typer.Option("--workers", help="Concurrent worker count.")] = 10,
    concurrent_updates: Annotated[
        int,
        typer.Option("--updates", help="Maximum UPDATE operations for concurrency scenario."),
    ] = 100,
    target_table: Annotated[str, typer.Option("--table", help="Target table name.")] = "products",
    target_column: Annotated[str, typer.Option("--column", help="Target numeric column.")] = "stock",
    read_ratio: Annotated[
        float,
        typer.Option("--read-ratio", help="RW-heavy read ratio from 0.0 to 1.0."),
    ] = 0.7,
    row_count: Annotated[
        int,
        typer.Option("--row-count", help="RW-heavy synthetic products/customers to prepare."),
    ] = 100,
    operation_limit: Annotated[
        int,
        typer.Option("--operations", help="RW-heavy maximum operations across all workers."),
    ] = 1000,
    slow_query_threshold_ms: Annotated[
        float,
        typer.Option("--slow-ms", help="RW-heavy slow query threshold in milliseconds."),
    ] = 100.0,
    migration_operation: Annotated[
        str,
        typer.Option("--migration-operation", help="Migration operation: add_column or create_index."),
    ] = "add_column",
    lock_timeout_ms: Annotated[
        int,
        typer.Option("--lock-timeout-ms", help="Migration lock timeout in milliseconds."),
    ] = 500,
    statement_timeout_ms: Annotated[
        int,
        typer.Option("--statement-timeout-ms", help="Migration statement timeout in milliseconds."),
    ] = 5000,
    hold_lock_ms: Annotated[
        int,
        typer.Option("--hold-lock-ms", help="Migration test-only lock hold in milliseconds."),
    ] = 0,
    tenants: Annotated[
        int,
        typer.Option("--tenants", help="Security scenario tenant count."),
    ] = 3,
    rows_per_tenant: Annotated[
        int,
        typer.Option("--rows-per-tenant", help="Security scenario rows per tenant."),
    ] = 10,
    fuzz_payload_limit: Annotated[
        int,
        typer.Option("--fuzz-payloads", help="Security scenario SQL injection fuzz payload limit."),
    ] = 8,
    output: Annotated[Path | None, typer.Option("--output", "-o", help="JSON report path.")] = None,
    output_dir: Annotated[
        Path | None,
        typer.Option("--output-dir", help="Directory for --all JSON reports."),
    ] = None,
    run_all: Annotated[
        bool,
        typer.Option("--all", help="Run all implemented scenarios sequentially."),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Validate config without starting embedded PostgreSQL."),
    ] = True,
    execute: Annotated[
        bool,
        typer.Option("--execute", help="Run the scenario against local embedded ShadowDB."),
    ] = False,
    data_dir: Annotated[
        Path | None,
        typer.Option("--data-dir", help="ShadowDB data directory. Defaults to .datawraith/shadow."),
    ] = None,
    database_url: Annotated[
        str | None,
        typer.Option(
            "--database-url",
            help=(
                "Use a local PostgreSQL URL instead of embedded pgserver. "
                "Defaults to DATAWRAITH_DATABASE_URL when set."
            ),
        ),
    ] = None,
) -> None:
    """Validate or execute an attack scenario."""
    try:
        selected_scenarios = _select_attack_scenarios(scenario=scenario, run_all=run_all)
    except DataWraithError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    if output is not None and len(selected_scenarios) > 1:
        typer.echo("--output is only valid for a single scenario; use --output-dir with --all.", err=True)
        raise typer.Exit(code=1)
    if output_dir is not None and len(selected_scenarios) == 1:
        typer.echo("--output-dir is only valid with --all.", err=True)
        raise typer.Exit(code=1)
    if (output is not None or output_dir is not None) and not execute:
        typer.echo(
            "--output/--output-dir requires --execute because dry-run does not produce a report.",
            err=True,
        )
        raise typer.Exit(code=1)

    configs: dict[str, ScenarioConfig] = {}
    for selected_scenario in selected_scenarios:
        try:
            configs[selected_scenario] = _build_attack_config(
                scenario=selected_scenario,
                duration=duration,
                workers=workers,
                concurrent_updates=concurrent_updates,
                target_table=target_table,
                target_column=target_column,
                read_ratio=read_ratio,
                row_count=row_count,
                operation_limit=operation_limit,
                slow_query_threshold_ms=slow_query_threshold_ms,
                migration_operation=migration_operation,
                lock_timeout_ms=lock_timeout_ms,
                statement_timeout_ms=statement_timeout_ms,
                hold_lock_ms=hold_lock_ms,
                tenants=tenants,
                rows_per_tenant=rows_per_tenant,
                fuzz_payload_limit=fuzz_payload_limit,
            )
        except ValueError as exc:
            typer.echo(f"Invalid {selected_scenario} config: {exc}", err=True)
            raise typer.Exit(code=1) from exc

    for selected_scenario, config in configs.items():
        typer.echo(f"Scenario: {selected_scenario}")
        typer.echo(f"Config: {config.model_dump(mode='json')}")

    if execute:
        target_data_dir = data_dir or get_settings().shadow_data_dir
        for selected_scenario, config in configs.items():
            try:
                result = asyncio.run(
                    _execute_attack(selected_scenario, config, target_data_dir, database_url)
                )
            except DataWraithError as exc:
                typer.echo(f"Attack failed: {exc}", err=True)
                raise typer.Exit(code=1) from exc
            typer.echo(render_result(result))
            report_path = _report_path_for(
                scenario=selected_scenario,
                output=output,
                output_dir=output_dir,
            )
            if report_path is not None:
                JSONExporter().export(result, report_path)
                typer.echo(f"Report written: {report_path}")
        return

    if dry_run:
        typer.echo("Dry-run only; pass --execute to run against local ShadowDB.")


@app.command()
def compare(
    baseline: Annotated[Path, typer.Argument(help="Baseline JSON report path.")],
    current: Annotated[Path, typer.Argument(help="Current JSON report path.")],
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Emit machine-readable comparison JSON."),
    ] = False,
) -> None:
    """Compare two DataWraith JSON reports."""
    try:
        comparison = compare_results(load_result(baseline), load_result(current))
    except DataWraithError as exc:
        typer.echo(f"Compare failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    if json_output:
        typer.echo(json.dumps(comparison.model_dump(mode="json"), indent=2))
    else:
        typer.echo(render_comparison(comparison))


@app.command()
def report(
    report_path: Annotated[Path, typer.Argument(help="Scenario JSON report path.")],
    report_format: Annotated[
        str,
        typer.Option("--format", help="Report format: sarif, junit, or pdf."),
    ],
    output: Annotated[Path, typer.Option("--output", "-o", help="Output report path.")],
) -> None:
    """Export a DataWraith JSON report to CI/security-friendly formats."""
    normalized_format = report_format.strip().lower()
    if normalized_format not in {"sarif", "junit", "pdf"}:
        typer.echo("Unsupported report format. Available: sarif, junit, pdf", err=True)
        raise typer.Exit(code=1)
    try:
        result = load_result(report_path)
        export_report(result, output, cast(ReportFormat, normalized_format))
    except DataWraithError as exc:
        typer.echo(f"Report export failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Report written: {output}")


@ai_app.command("setup")
def ai_setup(
    provider: Annotated[str, typer.Option("--provider", help="AI provider name.")] = "openai",
    api_key: Annotated[
        str,
        typer.Option("--api-key", prompt=True, hide_input=True, help="Provider API key."),
    ] = "",
) -> None:
    """Store an optional BYOK provider key in the OS keyring."""
    try:
        store_api_key(provider, api_key)
    except DataWraithError as exc:
        typer.echo(f"AI setup failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Stored {provider.strip().lower()} API key in OS keyring.")


@ai_app.command("status")
def ai_status(
    provider: Annotated[str, typer.Option("--provider", help="AI provider name.")] = "openai",
) -> None:
    """Show whether a BYOK provider key is configured."""
    try:
        configured = has_api_key(provider)
    except DataWraithError as exc:
        typer.echo(f"AI status failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    state = "configured" if configured else "not configured"
    typer.echo(f"{provider.strip().lower()}: {state}")


@ai_app.command("analyze")
def ai_analyze(
    report_path: Annotated[Path, typer.Argument(help="Scenario JSON report path.")],
    provider: Annotated[
        str | None,
        typer.Option("--provider", help="Optional BYOK provider for future AI enrichment."),
    ] = None,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Emit machine-readable suggestions."),
    ] = False,
) -> None:
    """Analyze a scenario report with offline rules and optional BYOK metadata."""
    try:
        suggestions = analyze_report(report_path, provider)
    except DataWraithError as exc:
        typer.echo(f"AI analyze failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    if json_output:
        typer.echo(json.dumps([item.model_dump(mode="json") for item in suggestions], indent=2))
        return

    for index, suggestion in enumerate(suggestions, start=1):
        typer.echo(f"{index}. [{suggestion.risk_level}] {suggestion.reasoning}")
        if suggestion.sql_fix:
            typer.echo(f"   SQL: {suggestion.sql_fix}")
        if suggestion.rollback_plan:
            typer.echo(f"   Rollback: {suggestion.rollback_plan}")


def _select_attack_scenarios(*, scenario: str | None, run_all: bool) -> list[str]:
    if run_all and scenario is not None:
        raise DataWraithError("Use either a scenario argument or --all, not both.")
    if run_all:
        return ["concurrency", "rw-heavy", "migration", "security"]
    if scenario is None:
        raise DataWraithError(
            "Provide a scenario or pass --all. Available: concurrency, rw-heavy, migration, security"
        )
    if scenario not in {"concurrency", "rw-heavy", "migration", "security"}:
        raise DataWraithError("Unknown scenario. Available: concurrency, rw-heavy, migration, security")
    return [scenario]


def _report_path_for(
    *,
    scenario: str,
    output: Path | None,
    output_dir: Path | None,
) -> Path | None:
    if output is not None:
        return output
    if output_dir is not None:
        return output_dir / f"{scenario}.json"
    return None


def _resolve_database_url(database_url: str | None) -> str | None:
    configured_url = database_url or get_settings().database_url
    if configured_url is None:
        return None
    return validate_local_database_url(configured_url)


def _create_shadow_db(data_dir: Path, database_url: str | None) -> ShadowDB:
    resolved_database_url = _resolve_database_url(database_url)
    if resolved_database_url is None:
        data_dir.mkdir(parents=True, exist_ok=True)
        return ShadowDB(data_dir=data_dir, cleanup_mode="stop")
    return ShadowDB(
        data_dir=data_dir,
        cleanup_mode="stop",
        external_url=resolved_database_url,
    )


def _run_quickstart(
    *,
    output_dir: Path,
    duration: int,
    workers: int,
    rows: int,
    operations: int,
    data_dir: Path,
    database_url: str | None,
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    db: ShadowDB | None = None
    try:
        db = _create_shadow_db(data_dir, database_url)
        db.start()
        asyncio.run(db.load_schema(QUICKSTART_SCHEMA_SQL))
        execute_seed_plan(
            db,
            SeedPlan(
                table=QUICKSTART_TABLE,
                rows=rows,
                columns=parse_column_specs(["id:int", "name:name", "stock:int"]),
            ),
        )
    finally:
        if db is not None:
            db.stop()

    quickstart_scenarios = ["concurrency", "rw-heavy", "migration", "security"]
    written_reports: list[Path] = []
    for scenario in quickstart_scenarios:
        config = _build_attack_config(
            scenario=scenario,
            duration=duration,
            workers=workers,
            concurrent_updates=max(10, rows),
            target_table=QUICKSTART_TABLE,
            target_column="stock",
            read_ratio=0.7,
            row_count=rows,
            operation_limit=operations,
            slow_query_threshold_ms=100.0,
            migration_operation="add_column",
            lock_timeout_ms=500,
            statement_timeout_ms=5000,
            hold_lock_ms=0,
            tenants=2,
            rows_per_tenant=2,
            fuzz_payload_limit=4,
        )
        result = asyncio.run(_execute_attack(scenario, config, data_dir, database_url))
        report_path = output_dir / f"{scenario}.json"
        JSONExporter().export(result, report_path)
        written_reports.append(report_path)

    security_report = output_dir / "security.json"
    for report_format, suffix in [
        ("sarif", "security.sarif"),
        ("junit", "security.xml"),
        ("pdf", "security.pdf"),
    ]:
        export_report(load_result(security_report), output_dir / suffix, cast(ReportFormat, report_format))
        written_reports.append(output_dir / suffix)

    return written_reports


def _build_attack_config(
    *,
    scenario: str,
    duration: int,
    workers: int,
    concurrent_updates: int,
    target_table: str,
    target_column: str,
    read_ratio: float,
    row_count: int,
    operation_limit: int,
    slow_query_threshold_ms: float,
    migration_operation: str,
    lock_timeout_ms: int,
    statement_timeout_ms: int,
    hold_lock_ms: int,
    tenants: int,
    rows_per_tenant: int,
    fuzz_payload_limit: int,
) -> ScenarioConfig:
    if scenario == "concurrency":
        return ConcurrencyConfig(
            duration_seconds=duration,
            workers=workers,
            concurrent_updates=concurrent_updates,
            target_table=target_table,
            target_column=target_column,
        )
    if scenario == "rw-heavy":
        return RWHeavyConfig(
            duration_seconds=duration,
            workers=workers,
            read_write_ratio=read_ratio,
            row_count=row_count,
            operation_limit=operation_limit,
            slow_query_threshold_ms=slow_query_threshold_ms,
        )
    if scenario == "security":
        return SecurityConfig(
            duration_seconds=duration,
            workers=workers,
            tenants=tenants,
            rows_per_tenant=rows_per_tenant,
            fuzz_payload_limit=fuzz_payload_limit,
        )
    migration_table = "dw_migration_items" if target_table == "products" else target_table
    migration_column = "phase3_flag" if target_column == "stock" else target_column
    return MigrationConfig(
        duration_seconds=duration,
        workers=workers,
        target_table=migration_table,
        target_column=migration_column,
        migration_operation=migration_operation,  # type: ignore[arg-type]
        row_count=row_count,
        operation_limit=operation_limit,
        lock_timeout_ms=lock_timeout_ms,
        statement_timeout_ms=statement_timeout_ms,
        hold_lock_ms=hold_lock_ms,
    )


def _collect_doctor_checks() -> list[tuple[str, bool, str]]:
    checks: list[tuple[str, bool, str]] = []
    database_url: str | None = None
    database_url_error: DataWraithError | None = None
    database_connection_error: str | None = None

    python_ok = sys.version_info >= (3, 12)
    checks.append(("Python", python_ok, sys.version.split()[0]))

    required_modules = ["pydantic", "typer", "textual", "psycopg", "asyncpg"]
    for module_name in required_modules:
        found = importlib.util.find_spec(module_name) is not None
        detail = "available" if found else "missing"
        checks.append((module_name, found, detail))

    try:
        database_url = _resolve_database_url(None)
        if database_url is not None:
            database_connection_error = _check_database_url_connection(database_url)
    except DataWraithError as exc:
        database_url_error = exc

    pgserver_found = importlib.util.find_spec("pgserver") is not None
    if pgserver_found:
        checks.append(("pgserver", True, "available"))
    elif database_url is not None and database_connection_error is None:
        checks.append(("pgserver", True, "unavailable; local PostgreSQL fallback configured"))
    elif database_url is not None:
        checks.append(("pgserver", False, "unavailable; local PostgreSQL fallback failed"))
    elif sys.version_info >= (3, 13):
        checks.append(
            (
                "pgserver",
                False,
                "unavailable on this Python; use Python 3.12 for embedded mode "
                "or configure DATAWRAITH_DATABASE_URL for local PostgreSQL",
            )
        )
    else:
        checks.append(("pgserver", False, "missing"))

    if database_url_error is not None:
        checks.append(("database_url", False, str(database_url_error)))
    elif database_connection_error is not None:
        checks.append(("database_url", False, database_connection_error))
    else:
        detail = "configured local PostgreSQL fallback" if database_url else "not configured"
        checks.append(("database_url", True, detail))

    return checks


def _check_database_url_connection(database_url: str) -> str | None:
    """Return a human-readable connection error for a local fallback URL."""
    try:
        with psycopg.connect(database_url, connect_timeout=5) as conn:
            conn.execute("SELECT 1")
    except psycopg.Error as exc:
        detail = str(exc).splitlines()[0]
        return f"configured but connection failed: {detail}"
    return None


async def _execute_attack(
    scenario: str,
    config: ScenarioConfig,
    data_dir: Path,
    database_url: str | None = None,
) -> ScenarioResult:
    db = _create_shadow_db(data_dir, database_url)
    db.start()
    final_result: ScenarioResult | None = None
    try:
        async for event in run_scenario(scenario, config, db=db):
            if event.type in {EventType.LOG, EventType.WARNING, EventType.ERROR} and event.message:
                typer.echo(event.message)
            if event.type == EventType.METRIC and event.data is not None:
                typer.echo(
                    "metrics "
                    f"completed={event.data.get('completed', 0)} "
                    f"reads={event.data.get('reads', '-')} "
                    f"writes={event.data.get('writes', '-')} "
                    f"errors={event.data.get('errors', 0)} "
                    f"deadlocks={event.data.get('deadlocks', 0)} "
                    f"qps={float(event.data.get('qps', 0.0)):.1f}"
                )
            if event.type == EventType.COMPLETED and event.data is not None:
                final_result = ScenarioResult.model_validate(event.data["result"])
    finally:
        db.stop()

    if final_result is None:
        raise DataWraithError("Scenario did not emit a completed result")
    return final_result
