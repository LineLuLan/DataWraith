from __future__ import annotations

from datawraith.engine.analyzer import SlowQuerySample, summarize_slow_queries


def test_summarize_slow_queries_groups_and_ranks_samples() -> None:
    culprits = summarize_slow_queries(
        [
            SlowQuerySample(
                label="read",
                query_text=(
                    "SELECT * FROM dw_products p "
                    "JOIN dw_orders o ON o.product_id = p.id GROUP BY p.category"
                ),
                duration_ms=120.0,
            ),
            SlowQuerySample(
                label="read",
                query_text=(
                    "SELECT * FROM dw_products p "
                    "JOIN dw_orders o ON o.product_id = p.id GROUP BY p.category"
                ),
                duration_ms=80.0,
            ),
            SlowQuerySample(
                label="update",
                query_text="UPDATE dw_products SET stock = stock - 1 WHERE id = $1",
                duration_ms=50.0,
            ),
        ]
    )

    assert len(culprits) == 2
    assert culprits[0].rank == 1
    assert culprits[0].calls == 2
    assert "dw_orders(product_id)" in culprits[0].execution_plan


def test_summarize_slow_queries_handles_empty_input() -> None:
    assert summarize_slow_queries([]) == []
