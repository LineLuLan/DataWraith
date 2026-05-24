"""Deterministic seed data planning for Phase 1."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from time import perf_counter
from typing import Any, Literal
from uuid import NAMESPACE_DNS, uuid5

from faker import Faker
from pydantic import BaseModel, ConfigDict, Field

from datawraith.core.exceptions import SeederError
from datawraith.core.shadow_db import ShadowDB
from datawraith.core.types import SeedResult

ColumnKind = Literal["int", "integer", "text", "email", "name", "uuid", "bool", "timestamp", "numeric"]


class ColumnSeedSpec(BaseModel):
    """Column generation spec."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(min_length=1)
    kind: ColumnKind


class SeedPlan(BaseModel):
    """A deterministic seed data plan."""

    model_config = ConfigDict(frozen=True)

    table: str = Field(min_length=1)
    rows: int = Field(ge=1, le=1_000_000)
    columns: tuple[ColumnSeedSpec, ...]
    seed: int = 100


def parse_column_specs(specs: list[str]) -> tuple[ColumnSeedSpec, ...]:
    """Parse CLI column specs like `id:int` and `email:email`."""
    parsed: list[ColumnSeedSpec] = []
    for spec in specs:
        if ":" not in spec:
            raise SeederError(f"Invalid column spec '{spec}'. Expected name:kind")
        name, kind = (part.strip() for part in spec.split(":", 1))
        if not name or not kind:
            raise SeederError(f"Invalid column spec '{spec}'. Expected name:kind")
        try:
            parsed.append(ColumnSeedSpec(name=name, kind=kind))  # type: ignore[arg-type]
        except ValueError as exc:
            raise SeederError(f"Invalid column kind in '{spec}'") from exc

    if not parsed:
        raise SeederError("At least one column spec is required")
    return tuple(parsed)


def generate_rows(plan: SeedPlan) -> list[dict[str, Any]]:
    """Generate deterministic preview rows for a seed plan."""
    return list(iter_rows(plan))


def iter_rows(plan: SeedPlan) -> Iterator[dict[str, Any]]:
    """Iterate deterministic rows for a seed plan without holding all in memory."""
    fake = Faker()
    Faker.seed(plan.seed)
    for row_index in range(plan.rows):
        row: dict[str, Any] = {}
        for column in plan.columns:
            row[column.name] = _value_for(column.kind, row_index=row_index, fake=fake, plan=plan)
        yield row


def render_insert_sql(plan: SeedPlan, max_rows: int = 20) -> str:
    """Render a safe SQL preview for the seed plan.

    The real high-volume seeder should use COPY/parameterized execution later.
    This preview is useful for tests, docs, and CLI dry-runs.
    """
    rows = generate_rows(plan.model_copy(update={"rows": min(plan.rows, max_rows)}))
    column_sql = ", ".join(quote_identifier(column.name) for column in plan.columns)
    value_lines = []
    for row in rows:
        values = ", ".join(sql_literal(row[column.name]) for column in plan.columns)
        value_lines.append(f"  ({values})")
    suffix = "" if plan.rows <= max_rows else f"\n-- Preview truncated to {max_rows} of {plan.rows} rows"
    return (
        f"INSERT INTO {quote_identifier(plan.table)} ({column_sql}) VALUES\n"
        + ",\n".join(value_lines)
        + ";"
        + suffix
    )


def execute_seed_plan(db: ShadowDB, plan: SeedPlan, batch_size: int = 1000) -> SeedResult:
    """Insert generated rows into a ShadowDB using parameterized batches."""
    if batch_size < 1:
        raise SeederError("batch_size must be >= 1")

    started = perf_counter()
    columns = list(plan.columns)
    column_sql = ", ".join(quote_identifier(column.name) for column in columns)
    placeholders = ", ".join(["%s"] * len(columns))
    sql = f"INSERT INTO {quote_identifier(plan.table)} ({column_sql}) VALUES ({placeholders})"
    inserted = 0
    batch: list[tuple[Any, ...]] = []

    with db.sync_connection() as conn:
        with conn.cursor() as cursor:
            for row in iter_rows(plan):
                batch.append(tuple(row[column.name] for column in columns))
                if len(batch) >= batch_size:
                    cursor.executemany(sql, batch)
                    inserted += len(batch)
                    batch = []
            if batch:
                cursor.executemany(sql, batch)
                inserted += len(batch)

    return SeedResult(
        table=plan.table,
        rows_requested=plan.rows,
        rows_inserted=inserted,
        duration_seconds=perf_counter() - started,
    )


def quote_identifier(identifier: str) -> str:
    """Quote a PostgreSQL identifier."""
    if "\x00" in identifier:
        raise SeederError("Identifier contains NUL byte")
    return '"' + identifier.replace('"', '""') + '"'


def sql_literal(value: Any) -> str:
    """Render a SQL literal for preview output only."""
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, int | float):
        return str(value)
    if isinstance(value, datetime):
        return "'" + value.isoformat().replace("'", "''") + "'"
    return "'" + str(value).replace("'", "''") + "'"


def _value_for(kind: ColumnKind, *, row_index: int, fake: Faker, plan: SeedPlan) -> Any:
    match kind:
        case "int" | "integer":
            return row_index + 1
        case "text":
            return fake.sentence(nb_words=4)
        case "email":
            return fake.unique.email()
        case "name":
            return fake.name()
        case "uuid":
            return str(uuid5(NAMESPACE_DNS, f"{plan.table}:{plan.seed}:{row_index}"))
        case "bool":
            return row_index % 2 == 0
        case "timestamp":
            return datetime(2026, 1, 1, tzinfo=UTC) + timedelta(seconds=row_index)
        case "numeric":
            return round((row_index + 1) * 1.11, 2)
