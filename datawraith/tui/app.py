"""Minimal useful Textual app for Phase 1."""

from __future__ import annotations

import importlib.util
import sys

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Footer, Header, Static

from datawraith import __version__
from datawraith.core.config import get_settings
from datawraith.tui import theme


def runtime_status_lines() -> list[str]:
    """Return human-readable local runtime status lines."""
    pgserver_available = importlib.util.find_spec("pgserver") is not None
    pgserver_status = "available" if pgserver_available else "unavailable; use Python 3.12"
    return [
        f"Python: {sys.version.split()[0]}",
        f"pgserver: {pgserver_status}",
        f"ShadowDB: {get_settings().shadow_data_dir}",
    ]


class DataWraithApp(App[None]):
    """DataWraith terminal UI."""

    TITLE = "DataWraith"
    SUB_TITLE = "PostgreSQL chaos-testing"
    CSS = f"""
    Screen {{
        background: {theme.BACKGROUND};
        color: {theme.TEXT};
    }}

    #layout {{
        height: 1fr;
        padding: 1 2;
        layout: vertical;
    }}

    .card {{
        width: 100%;
        border: round {theme.PRIMARY};
        background: {theme.SURFACE};
        padding: 1 2;
        margin-bottom: 1;
    }}

    #title {{
        color: {theme.PRIMARY};
        text-style: bold;
    }}

    #muted {{
        color: {theme.MUTED};
    }}

    .command {{
        color: {theme.SECONDARY};
    }}
    """

    BINDINGS = [("q", "quit", "Quit"), ("d", "toggle_dark", "Toggle theme")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="layout"):
            with Container(classes="card", id="status-card"):
                yield Static("DataWraith", id="title")
                yield Static(f"sdb v{__version__} - Phase 1/2 alpha")
                yield Static("\n".join(runtime_status_lines()), id="runtime-status")
            with Container(classes="card", id="attack-card"):
                yield Static("Concurrency Test", id="attack-title")
                yield Static(
                    "Default: dry-run only. Add --execute to run against local ShadowDB.",
                    id="muted",
                )
                yield Static(
                    "sdb attack concurrency --dry-run",
                    classes="command",
                    id="attack-command",
                )
                yield Static(
                    "sdb attack concurrency --execute --duration 10 --workers 2 "
                    "--updates 10 --output report.json",
                    classes="command",
                    id="attack-execute-command",
                )
            with Container(classes="card", id="rw-heavy-card"):
                yield Static("RW-heavy Test", id="rw-heavy-title")
                yield Static(
                    "Phase 2 mixed SELECT/INSERT/UPDATE workload. Execute requires Python 3.12 + pgserver.",
                    id="rw-heavy-muted",
                )
                yield Static(
                    "sdb attack rw-heavy --dry-run --row-count 10 --operations 20",
                    classes="command",
                    id="rw-heavy-command",
                )
                yield Static(
                    "sdb attack --all --execute --output-dir reports/",
                    classes="command",
                    id="attack-all-command",
                )
            with Container(classes="card", id="migration-card"):
                yield Static("Migration Lock Test", id="migration-title")
                yield Static(
                    "Phase 3 local DDL-under-load simulation. AI advice is BYOK and never auto-applied.",
                    id="migration-muted",
                )
                yield Static(
                    "sdb attack migration --dry-run --migration-operation add_column",
                    classes="command",
                    id="migration-command",
                )
                yield Static(
                    "sdb ai analyze migration.json --provider openai",
                    classes="command",
                    id="ai-analyze-command",
                )
            with Container(classes="card", id="security-card"):
                yield Static("Security & Isolation Test", id="security-title")
                yield Static(
                    "Phase 4 local tenant isolation, RLS, injection fuzz, and report exports.",
                    id="security-muted",
                )
                yield Static(
                    "sdb attack security --dry-run",
                    classes="command",
                    id="security-command",
                )
                yield Static(
                    "sdb report security.json --format sarif --output security.sarif",
                    classes="command",
                    id="report-export-command",
                )
            with Container(classes="card", id="report-card"):
                yield Static("Report Summary", id="report-title")
                yield Static(
                    "No report loaded yet. Run the execute command above to generate JSON.",
                    id="report-summary",
                )
                yield Static(
                    "Compare reports: sdb compare baseline.json current.json",
                    classes="command",
                    id="compare-command",
                )
        yield Footer()


def run() -> None:
    """Run the TUI."""
    DataWraithApp().run()
