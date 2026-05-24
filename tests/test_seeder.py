from __future__ import annotations

import pytest

from datawraith.core.exceptions import SeederError
from datawraith.engine.seeder import (
    SeedPlan,
    execute_seed_plan,
    generate_rows,
    parse_column_specs,
    render_insert_sql,
)


def test_parse_column_specs() -> None:
    columns = parse_column_specs(["id:int", "email:email"])

    assert columns[0].name == "id"
    assert columns[0].kind == "int"
    assert columns[1].kind == "email"


def test_parse_column_specs_rejects_invalid_input() -> None:
    with pytest.raises(SeederError):
        parse_column_specs(["missing-kind"])


def test_generate_rows_is_deterministic() -> None:
    plan = SeedPlan(
        table="users",
        rows=2,
        columns=parse_column_specs(["id:int", "email:email", "active:bool"]),
        seed=42,
    )

    first = generate_rows(plan)
    second = generate_rows(plan)

    assert first == second
    assert first[0]["id"] == 1
    assert first[0]["active"] is True


def test_render_insert_sql_quotes_identifiers_and_literals() -> None:
    plan = SeedPlan(
        table='odd"table',
        rows=1,
        columns=parse_column_specs(["id:int", "name:name"]),
        seed=1,
    )

    sql = render_insert_sql(plan)

    assert 'INSERT INTO "odd""table"' in sql
    assert '"id", "name"' in sql
    assert sql.endswith(";")


def test_execute_seed_plan_batches_rows() -> None:
    executed: list[tuple[str, list[tuple[object, ...]]]] = []

    class FakeCursor:
        def __enter__(self):  # type: ignore[no-untyped-def]
            return self

        def __exit__(self, *args):  # type: ignore[no-untyped-def]
            return None

        def executemany(self, sql: str, batch: list[tuple[object, ...]]) -> None:
            executed.append((sql, list(batch)))

    class FakeConnection:
        def __enter__(self):  # type: ignore[no-untyped-def]
            return self

        def __exit__(self, *args):  # type: ignore[no-untyped-def]
            return None

        def cursor(self) -> FakeCursor:
            return FakeCursor()

    class FakeDB:
        def sync_connection(self) -> FakeConnection:
            return FakeConnection()

    plan = SeedPlan(table="products", rows=3, columns=parse_column_specs(["id:int", "name:name"]))

    result = execute_seed_plan(FakeDB(), plan, batch_size=2)  # type: ignore[arg-type]

    assert result.rows_inserted == 3
    assert len(executed) == 2
    assert executed[0][0] == 'INSERT INTO "products" ("id", "name") VALUES (%s, %s)'
    assert len(executed[0][1]) == 2
