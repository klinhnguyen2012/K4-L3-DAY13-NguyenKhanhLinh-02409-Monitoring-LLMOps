from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from app.dashboard_runtime import summarize_records


def test_dashboard_summary_aggregates_six_contract_panels():
    now = datetime.now(timezone.utc)
    records = [
        {"ts": (now - timedelta(minutes=2)).isoformat(), "event": "request_received", "correlation_id": "a"},
        {"ts": (now - timedelta(minutes=1)).isoformat(), "event": "request_received", "correlation_id": "b"},
        {
            "ts": now.isoformat(), "event": "response_sent", "correlation_id": "a",
            "latency_ms": 1000, "ttft_ms": 100, "cost_usd": 0.02,
            "tokens_in": 10, "tokens_out": 20, "quality_score": 0.8,
            "tool_success": True,
        },
        {
            "ts": now.isoformat(), "event": "request_failed", "correlation_id": "b",
            "error_type": "RuntimeError", "tool_name": "retrieval", "tool_success": False,
        },
    ]

    summary = summarize_records(records, now=now)

    assert summary["latency"] == {"p50_ms": 1000.0, "p95_ms": 1000.0, "p99_ms": 1000.0, "ttft_p95_ms": 100.0}
    assert summary["traffic"]["requests"] == 2
    assert summary["traffic"]["requests_per_minute"] == round(2 / 60, 2)
    assert summary["errors"]["error_rate_pct"] == 50.0
    assert summary["errors"]["retrieval_success_pct"] == 50.0
    assert summary["cost"]["total_usd"] == 0.02
    assert sum(summary["cost"]["by_minute"].values()) == 0.02
    assert summary["tokens"] == {"input": 10, "output": 20}
    assert summary["quality"]["mean"] == 0.8


def test_dashboard_ignores_malformed_and_out_of_window_lines():
    now = datetime.now(timezone.utc)
    old = now - timedelta(hours=2)
    raw = "not json\n" + json.dumps({"ts": old.isoformat(), "event": "request_received"})
    from app.dashboard_runtime import parse_jsonl

    assert parse_jsonl(raw) == [{"ts": old.isoformat(), "event": "request_received"}]
    assert summarize_records(parse_jsonl(raw), now=now)["traffic"]["requests"] == 0
