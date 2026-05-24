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
def test_phase4_security_report_flow(tmp_path: Path) -> None:
    runner = CliRunner()
    data_dir = tmp_path / "shadow"
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
            "--data-dir",
            str(data_dir),
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
