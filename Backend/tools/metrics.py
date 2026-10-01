"""
Live request metrics: one small record per answered question, kept in Redis.

Offline evals say whether a change is good before it ships. These numbers say
how the deployed system is actually behaving: how long answers take, how often
it had to fall back to the web, how often an answer cites nothing from the code.

Only measurements are stored, never the question or the answer.
"""
from __future__ import annotations

import json
import logging
import time
from collections import deque
from typing import Any, Deque, Dict, List

logger = logging.getLogger(__name__)

KEY = "metrics:requests"
MAX_RECORDS = 5000
_memory: Deque[str] = deque(maxlen=MAX_RECORDS)   # used when Redis is not configured


def _redis():
    from config import redis_client
    return redis_client


def record(*, ok: bool, seconds: float = 0.0, route: str | None = None, web_used: bool = False,
           cached: bool = False, sources: int = 0, source: str = "app") -> None:
    """Stores one request. Never raises: metrics must not break an answer."""
    entry = json.dumps({"t": int(time.time()), "ok": ok, "seconds": round(seconds, 1), "route": route,
                        "web_used": web_used, "cached": cached, "sources": sources, "source": source})
    try:
        client = _redis()
        if client:
            client.lpush(KEY, entry)
            client.ltrim(KEY, 0, MAX_RECORDS - 1)
        else:
            _memory.appendleft(entry)
    except Exception as e:
        logger.warning(f"Could not record request metrics: {e}")


def _load() -> List[Dict[str, Any]]:
    try:
        client = _redis()
        raw = client.lrange(KEY, 0, MAX_RECORDS - 1) if client else list(_memory)
    except Exception as e:
        logger.warning(f"Could not read request metrics: {e}")
        raw = list(_memory)
    return [json.loads(r) for r in raw]


def _percentile(values: List[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, round(q * (len(ordered) - 1)))]


def _aggregate(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    answered = [r for r in rows if r["ok"]]
    # Researched answers are the ones retrieval quality applies to: not cached, not a greeting.
    researched = [r for r in answered if not r["cached"] and r["route"] not in (None, "simple_response")]
    times = [r["seconds"] for r in researched]

    def rate(part: int, whole: int) -> float | None:
        return round(part / whole, 3) if whole else None

    return {
        "requests": len(rows),
        "errors": len(rows) - len(answered),
        "error_rate": rate(len(rows) - len(answered), len(rows)),
        "cached": sum(1 for r in answered if r["cached"]),
        "researched": len(researched),
        "latency_p50_s": _percentile(times, 0.5),
        "latency_p95_s": _percentile(times, 0.95),
        "web_fallback_rate": rate(sum(1 for r in researched if r["web_used"]), len(researched)),
        "no_citation_rate": rate(sum(1 for r in researched if not r["sources"]), len(researched)),
        "routes": {route: sum(1 for r in answered if r["route"] == route)
                   for route in sorted({r["route"] or "unknown" for r in answered})} if answered else {},
    }


def summary(days: int = 7) -> Dict[str, Any]:
    """Totals for the window plus one row per day, from real users only (eval traffic is excluded)."""
    now = int(time.time())
    rows = [r for r in _load() if r.get("source") == "app" and r["t"] >= now - days * 86400]
    by_day: Dict[str, List[Dict[str, Any]]] = {}
    for r in rows:
        by_day.setdefault(time.strftime("%Y-%m-%d", time.gmtime(r["t"])), []).append(r)
    return {
        "window_days": days,
        "totals": _aggregate(rows),
        "daily": [{"day": day, **_aggregate(day_rows)} for day, day_rows in sorted(by_day.items())],
    }
