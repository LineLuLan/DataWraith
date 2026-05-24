"""Typer CLI entry point for DataWraith."""

from __future__ import annotations

import asyncio
import importlib.util
import json
import sys
from pathlib import Path
from typing import Annotated

import typer

from datawraith import __version__
from datawraith.core.config import get_settings
from datawraith.core.exceptions import DataWraithError
from datawraith.core.shadow_db import ShadowDB
from datawraith.core.types import (
    ConcurrencyConfig,
    EventType,
    RWHeavyConfig,
    ScenarioConfig,
    ScenarioResult,
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

app = typer.Typer(
    name="sdb",
    help="DataWraith PostgreSQL chaos-testing CLI.",
    invoke_without_command=True,
    no_args_is_help=False,
    pretty_exceptions_show_locals=False,
    rich_markup_mode="rich",
)


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
        target_data_dir.mkdir(parents=True, exist_ok=True)
        db = ShadowDB(data_dir=target_data_dir, cleanup_mode="stop")
        try:
            db.start()
            # Execute the original schema, not comment-stripped statements, so
            # PostgreSQL remains the source of truth for valid DDL syntax.
            asyncio.run(db.load_schema(schema_sql))
            loaded_tables = db.list_tables()
        except DataWraithError as exc:
            typer.echo(f"ShadowDB init failed: {exc}", err=True)
            raise typer.Exit(code=1) from exc
        finally:
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
) -> None:
    """Create a deterministic seed plan preview."""
    try:
        plan = SeedPlan(table=table, rows=rows, columns=parse_column_specs(columns))
    except DataWraithError as exc:
        typer.echo(f"Seeder error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    if execute:
        target_data_dir = data_dir or get_settings().shadow_data_dir
        db = ShadowDB(data_dir=target_data_dir, cleanup_mode="stop")
        try:
            db.start()
            result = execute_seed_plan(db, plan)
        except DataWraithError as exc:
            typer.echo(f"Seeder execution failed: {exc}", err=True)
            raise typer.Exit(code=1) from exc
        finally:
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
        typer.Argument(help="Scenario name. Supports concurrency and rw-heavy."),
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
                result = asyncio.run(_execute_attack(selected_scenario, config, target_data_dir))
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


def _select_attack_scenarios(*, scenario: str | None, run_all: bool) -> list[str]:
    if run_all and scenario is not None:
        raise DataWraithError("Use either a scenario argument or --all, not both.")
    if run_all:
        return ["concurrency", "rw-heavy"]
    if scenario is None:
        raise DataWraithError("Provide a scenario or pass --all. Available: concurrency, rw-heavy")
    if scenario not in {"concurrency", "rw-heavy"}:
        raise DataWraithError("Unknown scenario. Available: concurrency, rw-heavy")
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
) -> ScenarioConfig:
    if scenario == "concurrency":
        return ConcurrencyConfig(
            duration_seconds=duration,
            workers=workers,
            concurrent_updates=concurrent_updates,
            target_table=target_table,
            target_column=target_column,
        )
    return RWHeavyConfig(
        duration_seconds=duration,
        workers=workers,
        read_write_ratio=read_ratio,
        row_count=row_count,
        operation_limit=operation_limit,
        slow_query_threshold_ms=slow_query_threshold_ms,
    )


def _collect_doctor_checks() -> list[tuple[str, bool, str]]:
    checks: list[tuple[str, bool, str]] = []

    python_ok = sys.version_info >= (3, 12)
    checks.append(("Python", python_ok, sys.version.split()[0]))

    required_modules = ["pydantic", "typer", "textual", "psycopg", "asyncpg"]
    for module_name in required_modules:
        found = importlib.util.find_spec(module_name) is not None
        detail = "available" if found else "missing"
        checks.append((module_name, found, detail))

    pgserver_found = importlib.util.find_spec("pgserver") is not None
    if pgserver_found:
        checks.append(("pgserver", True, "available"))
    elif sys.version_info >= (3, 13):
        checks.append(("pgserver", False, "unavailable on this Python; use Python 3.12"))
    else:
        checks.append(("pgserver", False, "missing"))

    return checks


async def _execute_attack(
    scenario: str,
    config: ScenarioConfig,
    data_dir: Path,
) -> ScenarioResult:
    data_dir.mkdir(parents=True, exist_ok=True)
    db = ShadowDB(data_dir=data_dir, cleanup_mode="stop")
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
