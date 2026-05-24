from __future__ import annotations

import json
from datetime import datetime

from typer.testing import CliRunner

import datawraith.cli as cli_module
from datawraith.cli import app
from datawraith.core.types import HealthMetrics, ScenarioResult, ScenarioType, SeedResult


def test_version_option() -> None:
    result = CliRunner().invoke(app, ["--version"])

    assert result.exit_code == 0
    assert "DataWraith 0.1.0" in result.output


def test_doctor_command() -> None:
    result = CliRunner().invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert "Python" in result.output
    assert "pydantic" in result.output


def test_doctor_json_command() -> None:
    result = CliRunner().invoke(app, ["doctor", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert "checks" in payload
    assert any(check["name"] == "Python" for check in payload["checks"])


def test_doctor_json_accepts_local_database_url_fallback(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("DATAWRAITH_DATABASE_URL", "postgresql://localhost/datawraith")

    result = CliRunner().invoke(app, ["doctor", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    database_check = next(check for check in payload["checks"] if check["name"] == "database_url")
    assert database_check["ok"] is True
    assert database_check["detail"] == "configured local PostgreSQL fallback"


def test_recipes_command_prints_copy_paste_commands() -> None:
    result = CliRunner().invoke(app, ["recipes"])

    assert result.exit_code == 0
    assert "sdb quickstart --execute --output-dir reports" in result.output
    assert "docker compose up -d postgres" in result.output


def test_quickstart_dry_run_prints_guided_commands() -> None:
    result = CliRunner().invoke(app, ["quickstart"])

    assert result.exit_code == 0
    assert "Quickstart dry-run" in result.output
    assert "sdb recipes" in result.output


def test_quickstart_execute_writes_reports(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    calls: list[str] = []

    class FakeShadowDB:
        def __init__(self, data_dir, cleanup_mode):  # type: ignore[no-untyped-def]
            calls.append(f"db:{data_dir.name}:{cleanup_mode}")

        def start(self) -> str:
            calls.append("start")
            return "postgresql://example"

        async def load_schema(self, sql: str) -> None:
            calls.append(f"schema:{'dw_quickstart_products' in sql}")

        def stop(self) -> None:
            calls.append("stop")

    def fake_execute_seed_plan(db, plan):  # type: ignore[no-untyped-def]
        calls.append(f"seed:{plan.table}:{plan.rows}")
        return SeedResult(table=plan.table, rows_requested=plan.rows, rows_inserted=plan.rows, duration_seconds=0.1)

    async def fake_execute_attack(scenario, config, data_dir, database_url=None):  # type: ignore[no-untyped-def]
        calls.append(f"attack:{scenario}:{config.duration_seconds}:{data_dir.name}")
        scenario_type = {
            "concurrency": ScenarioType.CONCURRENCY,
            "rw-heavy": ScenarioType.RW_HEAVY,
            "migration": ScenarioType.MIGRATION,
            "security": ScenarioType.SECURITY,
        }[scenario]
        return ScenarioResult(
            scenario_name=scenario,
            scenario_type=scenario_type,
            config=config.model_dump(mode="json"),
            started_at=datetime(2026, 5, 24, 12, 0, 0),
            completed_at=datetime(2026, 5, 24, 12, 0, 1),
            duration_seconds=1.0,
            health_score=100,
            metrics=HealthMetrics(
                qps_max=2.0,
                qps_avg=2.0,
                latency_p50_ms=1.0,
                latency_p95_ms=1.0,
                latency_p99_ms=1.0,
                error_count=0,
                error_rate=0.0,
            ),
        )

    monkeypatch.setattr(cli_module, "ShadowDB", FakeShadowDB)
    monkeypatch.setattr(cli_module, "execute_seed_plan", fake_execute_seed_plan)
    monkeypatch.setattr(cli_module, "_execute_attack", fake_execute_attack)
    reports_dir = tmp_path / "reports"

    result = CliRunner().invoke(
        app,
        [
            "quickstart",
            "--execute",
            "--output-dir",
            str(reports_dir),
            "--data-dir",
            str(tmp_path / "shadow"),
        ],
    )

    assert result.exit_code == 0
    assert "Quickstart complete." in result.output
    assert (reports_dir / "concurrency.json").exists()
    assert (reports_dir / "rw-heavy.json").exists()
    assert (reports_dir / "migration.json").exists()
    assert (reports_dir / "security.json").exists()
    assert (reports_dir / "security.sarif").exists()
    assert "seed:dw_quickstart_products:10" in calls
    assert "attack:security:10:shadow" in calls


def test_init_command_dry_run(tmp_path) -> None:  # type: ignore[no-untyped-def]
    schema_path = tmp_path / "schema.sql"
    schema_path.write_text("CREATE TABLE products (id integer);", encoding="utf-8")

    result = CliRunner().invoke(app, ["init", str(schema_path)])

    assert result.exit_code == 0
    assert "Tables discovered: 1" in result.output
    assert "- products" in result.output


def test_init_command_execute_uses_shadow_db(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    schema_path = tmp_path / "schema.sql"
    schema_path.write_text("CREATE TABLE products (id integer);", encoding="utf-8")
    calls: list[str] = []

    class FakeShadowDB:
        def __init__(self, data_dir, cleanup_mode):  # type: ignore[no-untyped-def]
            calls.append(f"init:{data_dir.name}:{cleanup_mode}")

        def start(self) -> str:
            calls.append("start")
            return "postgresql://example"

        async def load_schema(self, sql: str) -> None:
            calls.append(f"load:{'products' in sql}")

        def list_tables(self) -> list[str]:
            calls.append("list")
            return ["products"]

        def stop(self) -> None:
            calls.append("stop")

    monkeypatch.setattr(cli_module, "ShadowDB", FakeShadowDB)

    result = CliRunner().invoke(
        app,
        ["init", str(schema_path), "--execute", "--data-dir", str(tmp_path / "shadow")],
    )

    assert result.exit_code == 0
    assert "Loaded tables: 1" in result.output
    assert "* products" in result.output
    assert calls == ["init:shadow:stop", "start", "load:True", "list", "stop"]


def test_seed_command_dry_run() -> None:
    result = CliRunner().invoke(
        app,
        ["seed", "--table", "products", "--column", "id:int", "--column", "name:name", "--rows", "1"],
    )

    assert result.exit_code == 0
    assert 'INSERT INTO "products"' in result.output


def test_seed_command_execute_uses_shadow_db(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    calls: list[str] = []

    class FakeShadowDB:
        def __init__(self, data_dir, cleanup_mode):  # type: ignore[no-untyped-def]
            calls.append(f"init:{data_dir.name}:{cleanup_mode}")

        def start(self) -> str:
            calls.append("start")
            return "postgresql://example"

        def stop(self) -> None:
            calls.append("stop")

    def fake_execute_seed_plan(db, plan):  # type: ignore[no-untyped-def]
        calls.append(f"seed:{plan.table}:{plan.rows}")
        return SeedResult(table=plan.table, rows_requested=plan.rows, rows_inserted=plan.rows, duration_seconds=0.1)

    monkeypatch.setattr(cli_module, "ShadowDB", FakeShadowDB)
    monkeypatch.setattr(cli_module, "execute_seed_plan", fake_execute_seed_plan)

    result = CliRunner().invoke(
        app,
        [
            "seed",
            "--table",
            "products",
            "--column",
            "id:int",
            "--rows",
            "2",
            "--execute",
            "--data-dir",
            str(tmp_path / "shadow"),
        ],
    )

    assert result.exit_code == 0
    assert "Inserted 2/2 rows into products" in result.output
    assert calls == ["init:shadow:stop", "start", "seed:products:2", "stop"]


def test_attack_command_dry_run() -> None:
    result = CliRunner().invoke(app, ["attack", "concurrency", "--dry-run"])

    assert result.exit_code == 0
    assert "Scenario: concurrency" in result.output


def test_attack_rw_heavy_dry_run() -> None:
    result = CliRunner().invoke(
        app,
        ["attack", "rw-heavy", "--dry-run", "--row-count", "10", "--operations", "5"],
    )

    assert result.exit_code == 0
    assert "Scenario: rw-heavy" in result.output
    assert "read_write_ratio" in result.output


def test_attack_all_dry_run_lists_configs() -> None:
    result = CliRunner().invoke(
        app,
        ["attack", "--all", "--dry-run", "--row-count", "10", "--operations", "5"],
    )

    assert result.exit_code == 0
    assert "Scenario: concurrency" in result.output
    assert "Scenario: rw-heavy" in result.output
    assert "Scenario: migration" in result.output
    assert "Scenario: security" in result.output


def test_attack_all_rejects_single_output_path(tmp_path) -> None:  # type: ignore[no-untyped-def]
    result = CliRunner().invoke(
        app,
        ["attack", "--all", "--output", str(tmp_path / "report.json")],
    )

    assert result.exit_code == 1
    assert "--output is only valid for a single scenario" in result.output


def test_attack_all_execute_writes_output_dir(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    calls: list[str] = []

    async def fake_execute_attack(scenario, config, data_dir, database_url=None):  # type: ignore[no-untyped-def]
        calls.append(f"{scenario}:{data_dir.name}")
        scenario_type = {
            "concurrency": ScenarioType.CONCURRENCY,
            "rw-heavy": ScenarioType.RW_HEAVY,
            "migration": ScenarioType.MIGRATION,
            "security": ScenarioType.SECURITY,
        }[scenario]
        return ScenarioResult(
            scenario_name=scenario,
            scenario_type=scenario_type,
            config=config.model_dump(mode="json"),
            started_at=datetime(2026, 5, 24, 12, 0, 0),
            completed_at=datetime(2026, 5, 24, 12, 0, 1),
            duration_seconds=1.0,
            health_score=100,
            metrics=HealthMetrics(
                qps_max=2.0,
                qps_avg=2.0,
                latency_p50_ms=1.0,
                latency_p95_ms=1.0,
                latency_p99_ms=1.0,
                error_count=0,
                error_rate=0.0,
            ),
        )

    monkeypatch.setattr(cli_module, "_execute_attack", fake_execute_attack)
    reports_dir = tmp_path / "reports"

    result = CliRunner().invoke(
        app,
        [
            "attack",
            "--all",
            "--execute",
            "--data-dir",
            str(tmp_path / "shadow"),
            "--output-dir",
            str(reports_dir),
            "--row-count",
            "10",
        ],
    )

    assert result.exit_code == 0
    assert calls == ["concurrency:shadow", "rw-heavy:shadow", "migration:shadow", "security:shadow"]
    assert (reports_dir / "concurrency.json").exists()
    assert (reports_dir / "rw-heavy.json").exists()
    assert (reports_dir / "migration.json").exists()
    assert (reports_dir / "security.json").exists()


def test_attack_migration_dry_run() -> None:
    result = CliRunner().invoke(
        app,
        [
            "attack",
            "migration",
            "--dry-run",
            "--row-count",
            "10",
            "--operations",
            "5",
            "--migration-operation",
            "add_column",
        ],
    )

    assert result.exit_code == 0
    assert "Scenario: migration" in result.output
    assert "phase3_flag" in result.output


def test_attack_security_dry_run() -> None:
    result = CliRunner().invoke(
        app,
        [
            "attack",
            "security",
            "--dry-run",
            "--tenants",
            "2",
            "--rows-per-tenant",
            "2",
            "--fuzz-payloads",
            "2",
        ],
    )

    assert result.exit_code == 0
    assert "Scenario: security" in result.output
    assert "dw_security_records" in result.output


def test_attack_output_requires_execute(tmp_path) -> None:  # type: ignore[no-untyped-def]
    result = CliRunner().invoke(
        app,
        ["attack", "concurrency", "--output", str(tmp_path / "report.json")],
    )

    assert result.exit_code == 1
    assert "--output/--output-dir requires --execute" in result.output


def test_attack_invalid_config_exits_nonzero() -> None:
    result = CliRunner().invoke(app, ["attack", "concurrency", "--workers", "0"])

    assert result.exit_code == 1
    assert "Invalid concurrency config" in result.output


def test_attack_execute_failure_is_user_friendly(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    async def fake_execute_attack(*args, **kwargs):  # type: ignore[no-untyped-def]
        from datawraith.core.exceptions import DataWraithError

        raise DataWraithError("pgserver unavailable")

    monkeypatch.setattr(cli_module, "_execute_attack", fake_execute_attack)

    result = CliRunner().invoke(
        app,
        ["attack", "concurrency", "--execute", "--data-dir", str(tmp_path / "shadow")],
    )

    assert result.exit_code == 1
    assert "Attack failed: pgserver unavailable" in result.output


def test_attack_command_execute_writes_output(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    async def fake_execute_attack(scenario, config, data_dir, database_url=None):  # type: ignore[no-untyped-def]
        assert scenario == "concurrency"
        assert config.workers == 2
        assert data_dir.name == "shadow"
        assert database_url is None
        return ScenarioResult(
            scenario_name="concurrency",
            scenario_type=ScenarioType.CONCURRENCY,
            config=config.model_dump(mode="json"),
            started_at=datetime(2026, 5, 24, 12, 0, 0),
            completed_at=datetime(2026, 5, 24, 12, 0, 1),
            duration_seconds=1.0,
            health_score=100,
            metrics=HealthMetrics(
                qps_max=2.0,
                qps_avg=2.0,
                latency_p50_ms=1.0,
                latency_p95_ms=1.0,
                latency_p99_ms=1.0,
                error_count=0,
                error_rate=0.0,
            ),
        )

    monkeypatch.setattr(cli_module, "_execute_attack", fake_execute_attack)
    report_path = tmp_path / "report.json"

    result = CliRunner().invoke(
        app,
        [
            "attack",
            "concurrency",
            "--workers",
            "2",
            "--execute",
            "--data-dir",
            str(tmp_path / "shadow"),
            "--output",
            str(report_path),
        ],
    )

    assert result.exit_code == 0
    assert "Health Score: 100/100" in result.output
    assert report_path.exists()


def test_attack_execute_accepts_local_database_url(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    captured: list[str | None] = []

    async def fake_execute_attack(scenario, config, data_dir, database_url=None):  # type: ignore[no-untyped-def]
        captured.append(database_url)
        return ScenarioResult(
            scenario_name=scenario,
            scenario_type=ScenarioType.CONCURRENCY,
            config=config.model_dump(mode="json"),
            started_at=datetime(2026, 5, 24, 12, 0, 0),
            completed_at=datetime(2026, 5, 24, 12, 0, 1),
            duration_seconds=1.0,
            health_score=100,
            metrics=HealthMetrics(
                qps_max=2.0,
                qps_avg=2.0,
                latency_p50_ms=1.0,
                latency_p95_ms=1.0,
                latency_p99_ms=1.0,
                error_count=0,
                error_rate=0.0,
            ),
        )

    monkeypatch.setattr(cli_module, "_execute_attack", fake_execute_attack)

    result = CliRunner().invoke(
        app,
        [
            "attack",
            "concurrency",
            "--execute",
            "--data-dir",
            str(tmp_path / "shadow"),
            "--database-url",
            "postgresql://localhost/datawraith",
        ],
    )

    assert result.exit_code == 0
    assert captured == ["postgresql://localhost/datawraith"]


def test_attack_execute_rejects_nonlocal_database_url(tmp_path) -> None:  # type: ignore[no-untyped-def]
    result = CliRunner().invoke(
        app,
        [
            "attack",
            "concurrency",
            "--execute",
            "--data-dir",
            str(tmp_path / "shadow"),
            "--database-url",
            "postgresql://db.example.com/prod",
        ],
    )

    assert result.exit_code == 1
    assert "only accepts local PostgreSQL URLs" in result.output


def test_compare_command_renders_report_delta(tmp_path) -> None:  # type: ignore[no-untyped-def]
    baseline = ScenarioResult(
        scenario_name="concurrency",
        scenario_type=ScenarioType.CONCURRENCY,
        config={"workers": 2},
        started_at=datetime(2026, 5, 24, 12, 0, 0),
        completed_at=datetime(2026, 5, 24, 12, 0, 1),
        duration_seconds=1.0,
        health_score=100,
        metrics=HealthMetrics(
            qps_max=2.0,
            qps_avg=2.0,
            latency_p50_ms=1.0,
            latency_p95_ms=2.0,
            latency_p99_ms=3.0,
            error_count=0,
            error_rate=0.0,
        ),
    )
    current = baseline.model_copy(update={"scenario_name": "rw-heavy", "health_score": 90})
    baseline_path = tmp_path / "baseline.json"
    current_path = tmp_path / "current.json"
    baseline_path.write_text(json.dumps(baseline.model_dump(mode="json")), encoding="utf-8")
    current_path.write_text(json.dumps(current.model_dump(mode="json")), encoding="utf-8")

    result = CliRunner().invoke(app, ["compare", str(baseline_path), str(current_path)])

    assert result.exit_code == 0
    assert "Comparing concurrency -> rw-heavy" in result.output
    assert "health_score" in result.output


def test_compare_command_json_output(tmp_path) -> None:  # type: ignore[no-untyped-def]
    baseline = ScenarioResult(
        scenario_name="concurrency",
        scenario_type=ScenarioType.CONCURRENCY,
        config={"workers": 2},
        started_at=datetime(2026, 5, 24, 12, 0, 0),
        completed_at=datetime(2026, 5, 24, 12, 0, 1),
        duration_seconds=1.0,
        health_score=100,
        metrics=HealthMetrics(
            qps_max=2.0,
            qps_avg=2.0,
            latency_p50_ms=1.0,
            latency_p95_ms=2.0,
            latency_p99_ms=3.0,
            error_count=0,
            error_rate=0.0,
        ),
    )
    baseline_path = tmp_path / "baseline.json"
    current_path = tmp_path / "current.json"
    payload = json.dumps(baseline.model_dump(mode="json"))
    baseline_path.write_text(payload, encoding="utf-8")
    current_path.write_text(payload, encoding="utf-8")

    result = CliRunner().invoke(
        app,
        ["compare", str(baseline_path), str(current_path), "--json"],
    )

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["baseline_scenario"] == "concurrency"
    assert data["deltas"][0]["name"] == "health_score"


def test_report_command_exports_sarif(tmp_path) -> None:  # type: ignore[no-untyped-def]
    report = ScenarioResult(
        scenario_name="security",
        scenario_type=ScenarioType.SECURITY,
        config={},
        started_at=datetime(2026, 5, 24, 12, 0, 0),
        completed_at=datetime(2026, 5, 24, 12, 0, 1),
        duration_seconds=1.0,
        health_score=100,
        metrics=HealthMetrics(
            qps_max=1.0,
            qps_avg=1.0,
            latency_p50_ms=0.0,
            latency_p95_ms=0.0,
            latency_p99_ms=0.0,
            error_count=0,
            error_rate=0.0,
        ),
    )
    report_path = tmp_path / "security.json"
    output_path = tmp_path / "security.sarif"
    report_path.write_text(json.dumps(report.model_dump(mode="json")), encoding="utf-8")

    result = CliRunner().invoke(
        app,
        ["report", str(report_path), "--format", "sarif", "--output", str(output_path)],
    )

    assert result.exit_code == 0
    assert output_path.exists()
    assert json.loads(output_path.read_text(encoding="utf-8"))["version"] == "2.1.0"


def test_ai_analyze_outputs_rule_based_suggestions(tmp_path) -> None:  # type: ignore[no-untyped-def]
    report = ScenarioResult(
        scenario_name="migration",
        scenario_type=ScenarioType.MIGRATION,
        config={"migration_operation": "add_column", "lock_timeout_ms": 500},
        started_at=datetime(2026, 5, 24, 12, 0, 0),
        completed_at=datetime(2026, 5, 24, 12, 0, 1),
        duration_seconds=1.0,
        health_score=90,
        metrics=HealthMetrics(
            qps_max=2.0,
            qps_avg=2.0,
            latency_p50_ms=1.0,
            latency_p95_ms=2.0,
            latency_p99_ms=3.0,
            error_count=1,
            error_rate=0.1,
            lock_wait_ms_total=50.0,
        ),
    )
    report_path = tmp_path / "migration.json"
    report_path.write_text(json.dumps(report.model_dump(mode="json")), encoding="utf-8")

    result = CliRunner().invoke(app, ["ai", "analyze", str(report_path), "--json"])

    assert result.exit_code == 0
    suggestions = json.loads(result.output)
    assert suggestions[0]["provider"] == "rules"
    assert "Adding nullable columns" in suggestions[0]["reasoning"]


def test_ai_status_uses_provider_key_state(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_module, "has_api_key", lambda provider: provider == "openai")

    result = CliRunner().invoke(app, ["ai", "status", "--provider", "openai"])

    assert result.exit_code == 0
    assert "openai: configured" in result.output


def test_ai_setup_stores_key(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    calls: list[tuple[str, str]] = []
    monkeypatch.setattr(cli_module, "store_api_key", lambda provider, api_key: calls.append((provider, api_key)))

    result = CliRunner().invoke(
        app,
        ["ai", "setup", "--provider", "openai", "--api-key", "sk-test"],
    )

    assert result.exit_code == 0
    assert calls == [("openai", "sk-test")]
