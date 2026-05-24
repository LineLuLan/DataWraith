from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from datawraith.cli import app
from tests.e2e_helpers import runtime_args


def test_phase4_security_report_flow(tmp_path: Path) -> None:
    runner = CliRunner()
    db_args = runtime_args(tmp_path)
    report_path = tmp_path / "security.json"
    sarif_path = tmp_path / "security.sarif"
    junit_path = tmp_path / "security.xml"
    pdf_path = tmp_path / "security.pdf"

    attack_result = runner.invoke(
        app,
        [
            "attack",
            "security",
            "--execute",
            "--duration",
            "10",
            "--tenants",
            "2",
            "--rows-per-tenant",
            "2",
            "--output",
            str(report_path),
            *db_args,
        ],
    )
    assert attack_result.exit_code == 0, attack_result.output

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["scenario_type"] == "security"

    for report_format, output_path in [
        ("sarif", sarif_path),
        ("junit", junit_path),
        ("pdf", pdf_path),
    ]:
        export_result = runner.invoke(
            app,
            [
                "report",
                str(report_path),
                "--format",
                report_format,
                "--output",
                str(output_path),
            ],
        )
        assert export_result.exit_code == 0, export_result.output
        assert output_path.exists()
