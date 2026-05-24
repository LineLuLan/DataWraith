from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from datawraith.cli import app
from tests.e2e_helpers import runtime_args


def test_phase1_alpha_cli_flow(tmp_path: Path) -> None:
    runner = CliRunner()
    db_args = runtime_args(tmp_path)
    report_path = tmp_path / "report.json"

    init_result = runner.invoke(
        app,
        [
            "init",
            "tests/fixtures/sample_schema.sql",
            "--execute",
            *db_args,
        ],
    )
    assert init_result.exit_code == 0, init_result.output

    seed_result = runner.invoke(
        app,
        [
            "seed",
            "--table",
            "products",
            "--column",
            "id:int",
            "--column",
            "name:name",
            "--column",
            "stock:int",
            "--rows",
            "10",
            "--execute",
            *db_args,
        ],
    )
    assert seed_result.exit_code == 0, seed_result.output

    attack_result = runner.invoke(
        app,
        [
            "attack",
            "concurrency",
            "--execute",
            "--duration",
            "10",
            "--workers",
            "2",
            "--updates",
            "10",
            "--output",
            str(report_path),
            *db_args,
        ],
    )
    assert attack_result.exit_code == 0, attack_result.output

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["scenario_type"] == "concurrency"
    assert report["metrics"]["qps_avg"] > 0
