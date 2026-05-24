"""Multi-format report exporters for Phase 4."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal
from xml.sax.saxutils import escape

from datawraith.core.exceptions import DataWraithError
from datawraith.core.types import Culprit, ScenarioResult

ReportFormat = Literal["sarif", "junit", "pdf"]


def export_report(result: ScenarioResult, output_path: Path, report_format: ReportFormat) -> None:
    """Export a ScenarioResult as SARIF, JUnit XML, or a minimal PDF."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if report_format == "sarif":
        output_path.write_text(json.dumps(_sarif_payload(result), indent=2) + "\n", encoding="utf-8")
        return
    if report_format == "junit":
        output_path.write_text(_junit_xml(result), encoding="utf-8")
        return
    if report_format == "pdf":
        output_path.write_bytes(_minimal_pdf(result))
        return
    raise DataWraithError(f"Unsupported report format: {report_format}")


def _sarif_payload(result: ScenarioResult) -> dict[str, object]:
    rules = [_sarif_rule(culprit) for culprit in result.top_culprits]
    sarif_results = [_sarif_result(culprit) for culprit in result.top_culprits]
    return {
        "version": "2.1.0",
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "DataWraith",
                        "informationUri": "https://datawraith.dev",
                        "rules": rules,
                    }
                },
                "results": sarif_results,
                "properties": {
                    "scenario": result.scenario_name,
                    "scenarioType": result.scenario_type,
                    "healthScore": result.health_score,
                },
            }
        ],
    }


def _sarif_rule(culprit: Culprit) -> dict[str, object]:
    rule_id = _rule_id(culprit)
    return {
        "id": rule_id,
        "name": rule_id,
        "shortDescription": {"text": culprit.query_text[:80]},
        "fullDescription": {"text": culprit.execution_plan},
        "defaultConfiguration": {"level": _sarif_level(culprit.impact_pct)},
    }


def _sarif_result(culprit: Culprit) -> dict[str, object]:
    return {
        "ruleId": _rule_id(culprit),
        "level": _sarif_level(culprit.impact_pct),
        "message": {"text": culprit.execution_plan},
        "locations": [
            {
                "physicalLocation": {
                    "artifactLocation": {"uri": "datawraith-report"},
                    "region": {"startLine": max(culprit.rank, 1)},
                }
            }
        ],
    }


def _junit_xml(result: ScenarioResult) -> str:
    failures = [culprit for culprit in result.top_culprits if culprit.impact_pct >= 50]
    lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        (
            f'<testsuite name="datawraith.{escape(result.scenario_name)}" '
            f'tests="{max(len(result.top_culprits), 1)}" failures="{len(failures)}">'
        ),
    ]
    if not result.top_culprits:
        lines.append(
            f'  <testcase classname="datawraith.{escape(result.scenario_name)}" '
            'name="no-findings" />'
        )
    for culprit in result.top_culprits:
        lines.append(
            f'  <testcase classname="datawraith.{escape(result.scenario_name)}" '
            f'name="{escape(_rule_id(culprit))}">'
        )
        if culprit.impact_pct >= 50:
            lines.append(
                f'    <failure message="{escape(culprit.query_text[:120])}">'
                f"{escape(culprit.execution_plan)}</failure>"
            )
        lines.append("  </testcase>")
    lines.append("</testsuite>")
    return "\n".join(lines) + "\n"


def _minimal_pdf(result: ScenarioResult) -> bytes:
    text_lines = [
        "DataWraith Report",
        f"Scenario: {result.scenario_name}",
        f"Health Score: {result.health_score}/100",
        f"Errors: {result.metrics.error_count}",
        f"QPS Avg: {result.metrics.qps_avg:.2f}",
        "Findings:",
    ]
    if not result.top_culprits:
        text_lines.append("- None recorded")
    for culprit in result.top_culprits[:8]:
        text_lines.append(f"- {_rule_id(culprit)}: {culprit.query_text[:70]}")
    stream = _pdf_text_stream(text_lines)
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    return _assemble_pdf(objects)


def _pdf_text_stream(lines: list[str]) -> bytes:
    escaped_lines = [_escape_pdf_text(line) for line in lines]
    commands = ["BT", "/F1 12 Tf", "72 740 Td"]
    for index, line in enumerate(escaped_lines):
        if index:
            commands.append("0 -18 Td")
        commands.append(f"({line}) Tj")
    commands.append("ET")
    return "\n".join(commands).encode("latin-1", errors="replace")


def _assemble_pdf(objects: list[bytes]) -> bytes:
    content = bytearray(b"%PDF-1.4\n")
    offsets: list[int] = []
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(content))
        content.extend(f"{index} 0 obj\n".encode("ascii"))
        content.extend(obj)
        content.extend(b"\nendobj\n")
    xref_offset = len(content)
    content.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    content.extend(b"0000000000 65535 f \n")
    for offset in offsets:
        content.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    content.extend(
        (
            "trailer\n"
            f"<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            "startxref\n"
            f"{xref_offset}\n"
            "%%EOF\n"
        ).encode("ascii")
    )
    return bytes(content)


def _rule_id(culprit: Culprit) -> str:
    return f"DW-{culprit.rank:03d}"


def _sarif_level(impact_pct: float) -> str:
    if impact_pct >= 80:
        return "error"
    if impact_pct >= 50:
        return "warning"
    return "note"


def _escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
