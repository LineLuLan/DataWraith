from __future__ import annotations

import pytest

from datawraith.core.exceptions import SchemaError
from datawraith.engine.schema_parser import parse_schema, split_sql_statements, strip_sql_comments


def test_parse_schema_discovers_tables() -> None:
    summary = parse_schema(
        """
        -- product catalog
        CREATE TABLE public.products (
            id integer primary key,
            name text not null
        );
        CREATE TABLE "order items" (id integer);
        """
    )

    assert summary.statement_count == 2
    assert [table.name for table in summary.tables] == ["public.products", "order items"]
    assert summary.warnings == []


def test_parse_schema_rejects_dangerous_statements() -> None:
    with pytest.raises(SchemaError, match="dangerous"):
        parse_schema("DROP DATABASE prod;")


def test_split_sql_statements_ignores_semicolon_inside_string() -> None:
    statements = split_sql_statements("CREATE TABLE logs (msg text DEFAULT 'a;b'); SELECT 1;")

    assert len(statements) == 2
    assert "a;b" in statements[0]


def test_strip_sql_comments() -> None:
    cleaned = strip_sql_comments("/* hidden */ CREATE TABLE t(id int); -- trailing")

    assert "hidden" not in cleaned
    assert "trailing" not in cleaned
