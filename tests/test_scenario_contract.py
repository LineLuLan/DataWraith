from __future__ import annotations

import pytest

import datawraith.engine.scenarios.concurrency as concurrency_module
from datawraith.core.types import ConcurrencyConfig, EventType
from datawraith.engine.scenarios import get_scenario
from datawraith.engine.scenarios.concurrency import ConcurrencyScenario
from datawraith.engine.scenarios.rw_heavy import RWHeavyScenario


@pytest.mark.asyncio
async def test_concurrency_scenario_completes(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    class FakeDB:
        def get_uri(self) -> str:
            return "postgresql://example"

    class FakeConnection:
        async def fetchval(self, query: str) -> int:
            assert "count" in query.lower()
            return 3

        async def execute(self, query: str, row_id: int) -> str:
            assert "UPDATE" in query
            assert row_id >= 1
            return "UPDATE 1"

        async def close(self) -> None:
            return None

    async def fake_connect(uri: str) -> FakeConnection:
        assert uri == "postgresql://example"
        return FakeConnection()

    monkeypatch.setattr(concurrency_module.asyncpg, "connect", fake_connect)
    config = ConcurrencyConfig(
        duration_seconds=10,
        workers=2,
        concurrent_updates=10,
        target_table="products",
        target_column="stock",
    )
    scenario = ConcurrencyScenario(db=FakeDB(), config=config)  # type: ignore[arg-type]

    events = [event async for event in scenario.run()]

    assert scenario.validate_config() == []
    assert events[0].type == EventType.STARTED
    assert events[-1].type == EventType.COMPLETED
    assert events[-1].data is not None
    assert events[-1].data["result"]["scenario_type"] == "concurrency"
    assert events[-1].data["result"]["metrics"]["qps_avg"] > 0


def test_concurrency_scenario_requires_shadow_db() -> None:
    config = ConcurrencyConfig(
        duration_seconds=10,
        workers=2,
        concurrent_updates=10,
        target_table="products",
        target_column="stock",
    )
    scenario = ConcurrencyScenario(db=None, config=config)

    assert "ShadowDB is required to run concurrency test" in scenario.validate_config()


def test_scenario_registry_returns_concurrency() -> None:
    assert get_scenario("concurrency") is ConcurrencyScenario


def test_scenario_registry_returns_rw_heavy() -> None:
    assert get_scenario("rw-heavy") is RWHeavyScenario


def test_scenario_registry_rejects_unknown() -> None:
    with pytest.raises(ValueError, match="Unknown scenario"):
        get_scenario("missing")
