from __future__ import annotations

import json
import math
from datetime import datetime, timedelta, timezone
from statistics import mean
from typing import Any


def parse_jsonl(raw: str) -> list[dict[str, Any]]:
    records = []
    for line in raw.splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            records.append(item)
    return records


def _percentile(values: list[float], percentile: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(percentile / 100 * len(ordered)) - 1))
    return float(ordered[index])


def summarize_records(
    records: list[dict[str, Any]], *, now: datetime | None = None, window_minutes: int = 60
) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=window_minutes)
    recent = []
    for record in records:
        try:
            timestamp = datetime.fromisoformat(str(record.get("ts", "")).replace("Z", "+00:00"))
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if cutoff <= timestamp <= now:
            recent.append(record)

    responses = [r for r in recent if r.get("event") == "response_sent"]
    requests = [r for r in recent if r.get("event") == "request_received"]
    failures = [r for r in recent if r.get("event") == "request_failed"]
    latencies = [float(r["latency_ms"]) for r in responses if isinstance(r.get("latency_ms"), (int, float))]
    ttfts = [float(r["ttft_ms"]) for r in responses if isinstance(r.get("ttft_ms"), (int, float))]
    tool_results = [r["tool_success"] for r in responses if isinstance(r.get("tool_success"), bool)]
    costs = [float(r["cost_usd"]) for r in responses if isinstance(r.get("cost_usd"), (int, float))]
    quality = [float(r["quality_score"]) for r in responses if isinstance(r.get("quality_score"), (int, float))]
    error_breakdown: dict[str, int] = {}
    for record in failures:
        name = str(record.get("error_type") or "unknown")
        error_breakdown[name] = error_breakdown.get(name, 0) + 1
    buckets: dict[str, int] = {}
    cost_buckets: dict[str, float] = {}
    for record in requests:
        try:
            timestamp = datetime.fromisoformat(str(record["ts"]).replace("Z", "+00:00"))
            key = timestamp.astimezone(timezone.utc).strftime("%H:%M")
            buckets[key] = buckets.get(key, 0) + 1
        except (KeyError, ValueError):
            continue
    for record in responses:
        try:
            timestamp = datetime.fromisoformat(str(record["ts"]).replace("Z", "+00:00"))
            key = timestamp.astimezone(timezone.utc).strftime("%H:%M")
            cost_buckets[key] = cost_buckets.get(key, 0.0) + float(record.get("cost_usd", 0))
        except (KeyError, ValueError, TypeError):
            continue

    return {
        "window_minutes": window_minutes,
        "generated_at": now.isoformat(),
        "records": len(recent),
        "latency": {"p50_ms": _percentile(latencies, 50), "p95_ms": _percentile(latencies, 95),
                    "p99_ms": _percentile(latencies, 99), "ttft_p95_ms": _percentile(ttfts, 95)},
        "traffic": {"requests": len(requests), "requests_per_minute": round(len(requests) / window_minutes, 2),
                    "by_minute": buckets},
        "errors": {"error_rate_pct": round(100 * len(failures) / len(requests), 2) if requests else 0,
                   "failed": len(failures), "breakdown": error_breakdown,
                   "retrieval_success_pct": round(100 * sum(tool_results) / len(tool_results), 2) if tool_results else 0},
        "cost": {"total_usd": round(sum(costs), 6), "by_minute": {k: round(v, 6) for k, v in cost_buckets.items()}},
        "tokens": {"input": sum(int(r.get("tokens_in", 0)) for r in responses if isinstance(r.get("tokens_in", 0), (int, float))),
                   "output": sum(int(r.get("tokens_out", 0)) for r in responses if isinstance(r.get("tokens_out", 0), (int, float)))},
        "quality": {"mean": round(mean(quality), 4) if quality else 0, "samples": len(quality)},
    }
