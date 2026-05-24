from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from datawraith.cli import app
from tests.e2e_helpers import runtime_args


def test_phase2_rw_heavy_cli_flow(tmp_path: Path) -> None:
    runner = CliRunner()
    db_args = runtime_args(tmp_path)
    report_path = tmp_path / "rw-heavy.json"

    attack_result = runner.invoke(
        app,
        [
            "attack",
            "rw-heavy",
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
            *db_args,
        ],
    )
    assert attack_result.exit_code == 0, attack_result.output

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["scenario_type"] == "rw_heavy"
    assert report["metrics"]["qps_avg"] > 0

    compare_result = runner.invoke(app, ["compare", str(report_path), str(report_path)])
    assert compare_result.exit_code == 0, compare_result.output
    assert "Comparing rw-heavy -> rw-heavy" in compare_result.output


def test_phase2_attack_all_cli_flow(tmp_path: Path) -> None:
    runner = CliRunner()
    db_args = runtime_args(tmp_path)
    reports_dir = tmp_path / "reports"

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
            "--all",
            "--execute",
            "--duration",
            "10",
            "--workers",
            "2",
            "--updates",
            "10",
            "--row-count",
            "10",
            "--operations",
            "20",
            "--output-dir",
            str(reports_dir),
            *db_args,
        ],
    )
    assert attack_result.exit_code == 0, attack_result.output
    assert (reports_dir / "concurrency.json").exists()
    assert (reports_dir / "rw-heavy.json").exists()
    assert (reports_dir / "migration.json").exists()
    assert (reports_dir / "security.json").exists()
