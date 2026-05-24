"""JSON report exporter."""

from __future__ import annotations

import json
from pathlib import Path

from datawraith.core.types import ScenarioResult
from datawraith.output.base import Exporter


class JSONExporter(Exporter):
    """Export `ScenarioResult` as JSON."""

    format = "json"
    extension = ".json"

    def export(self, result: ScenarioResult, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as file:
            json.dump(result.model_dump(mode="json"), file, indent=2)
            file.write("\n")
