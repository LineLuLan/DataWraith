"""Lightweight SQL schema parser for Phase 1 bootstrap flows."""

from __future__ import annotations

import re

from pydantic import BaseModel, Field

from datawraith.core.exceptions import SchemaError

_CREATE_TABLE_RE = re.compile(
    r"create\s+(?:temporary\s+|temp\s+|unlogged\s+)?table\s+"
    r"(?:if\s+not\s+exists\s+)?(?P<name>(?:\"[^\"]+\"|\w+)(?:\.(?:\"[^\"]+\"|\w+))?)",
    re.IGNORECASE,
)
_BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
_LINE_COMMENT_RE = re.compile(r"--[^\n\r]*")
_DANGEROUS_RE = re.compile(
    r"\b(drop\s+database|truncate\b|delete\s+from\b|alter\s+system\b)\b",
    re.IGNORECASE,
)


class TableSummary(BaseModel):
    """Summary of a table discovered in a schema file."""

    name: str
    statement_index: int = Field(ge=0)


class SchemaSummary(BaseModel):
    """Parsed schema summary used by CLI/TUI before loading into ShadowDB."""

    statements: list[str]
    tables: list[TableSummary]
    warnings: list[str] = Field(default_factory=list)

    @property
    def statement_count(self) -> int:
        """Return the number of executable statements."""
        return len(self.statements)


def parse_schema(sql: str) -> SchemaSummary:
    """Parse SQL DDL into a safe summary.

    This is intentionally lightweight. It is not a full SQL parser; it provides
    enough structure for Phase 1 init/seed UX while rejecting obviously unsafe
    production-style statements before any execution path is added.
    """
    cleaned = strip_sql_comments(sql).strip()
    if not cleaned:
        raise SchemaError("Schema SQL is empty")
    if _DANGEROUS_RE.search(cleaned):
        raise SchemaError("Schema contains dangerous statements not allowed in DataWraith init")

    statements = split_sql_statements(cleaned)
    if not statements:
        raise SchemaError("Schema SQL contains no executable statements")

    tables: list[TableSummary] = []
    warnings: list[str] = []
    for index, statement in enumerate(statements):
        match = _CREATE_TABLE_RE.search(statement)
        if match is not None:
            tables.append(TableSummary(name=_normalize_identifier(match.group("name")), statement_index=index))

    if not tables:
        warnings.append("No CREATE TABLE statements found")

    return SchemaSummary(statements=statements, tables=tables, warnings=warnings)


def strip_sql_comments(sql: str) -> str:
    """Remove block and line comments from SQL text."""
    without_blocks = _BLOCK_COMMENT_RE.sub("", sql)
    return _LINE_COMMENT_RE.sub("", without_blocks)


def split_sql_statements(sql: str) -> list[str]:
    """Split SQL statements on semicolons outside string literals."""
    statements: list[str] = []
    current: list[str] = []
    in_single_quote = False
    in_double_quote = False
    index = 0

    while index < len(sql):
        char = sql[index]
        next_char = sql[index + 1] if index + 1 < len(sql) else ""

        if char == "'" and not in_double_quote:
            current.append(char)
            if in_single_quote and next_char == "'":
                current.append(next_char)
                index += 2
                continue
            in_single_quote = not in_single_quote
            index += 1
            continue

        if char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
            current.append(char)
            index += 1
            continue

        if char == ";" and not in_single_quote and not in_double_quote:
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []
            index += 1
            continue

        current.append(char)
        index += 1

    tail = "".join(current).strip()
    if tail:
        statements.append(tail)
    return statements


def _normalize_identifier(identifier: str) -> str:
    parts = identifier.split(".")
    return ".".join(part.strip('"') for part in parts)
