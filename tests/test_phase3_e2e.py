from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from datawraith.cli import app


def pgserver_available() -> bool:
    return importlib.util.find_spec("pgserver") is not None


@pytest.mark.skipif(not pgserver_available(), reason="pgserver unavailable for this Python runtime")
def test_phase3_migration_cli_flow(tmp_path: Path) -> None:
    runner = CliRunner()
    data_dir = tmp_path / "shadow"
    report_path = tmp_path / "migration.json"

    attack_result = runner.invoke(
        app,
        [
            "attack",
            "migration",
            "--execute",
            "--duration",
            "10",
            "--workers",
            "2",
            "--row-count",
            "10",
            "--operations",
            "20",
            "--output",
            str(report_path),
            "--data-dir",
            str(data_dir),
        ],
    )
    assert attack_result.exit_code == 0, attack_result.output

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["scenario_type"] == "migration"

    analyze_result = runner.invoke(app, ["ai", "analyze", str(report_path), "--json"])
    assert analyze_result.exit_code == 0, analyze_result.output
    suggestions = json.loads(analyze_result.output)
    assert suggestions
