from __future__ import annotations

import pytest
from textual.widgets import Static

from datawraith.tui.app import DataWraithApp, runtime_status_lines


def test_runtime_status_lines_include_core_state() -> None:
    lines = runtime_status_lines()

    assert any(line.startswith("Python:") for line in lines)
    assert any(line.startswith("pgserver:") for line in lines)
    assert any(line.startswith("ShadowDB:") for line in lines)


@pytest.mark.asyncio
async def test_tui_composes_phase1_cards() -> None:
    app = DataWraithApp()

    async with app.run_test() as pilot:
        assert pilot.app.query_one("#runtime-status", Static) is not None
        assert pilot.app.query_one("#attack-command", Static) is not None
        assert pilot.app.query_one("#attack-execute-command", Static) is not None
        assert pilot.app.query_one("#rw-heavy-command", Static) is not None
        assert pilot.app.query_one("#attack-all-command", Static) is not None
        assert pilot.app.query_one("#compare-command", Static) is not None
        assert pilot.app.query_one("#report-summary", Static) is not None
