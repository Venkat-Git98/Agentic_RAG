"""Shared helpers for the eval scripts: dataset loading, matching, result files."""
from __future__ import annotations

import json
import logging
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

EVALS_DIR = Path(__file__).resolve().parent
BACKEND_DIR = EVALS_DIR.parent
GOLDEN_PATH = EVALS_DIR / "golden.jsonl"
RESULTS_DIR = EVALS_DIR / "results"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def quiet_logging() -> None:
    """The app logs at DEBUG; evals only want their own output."""
    logging.disable(logging.WARNING)


def load_golden(types: Iterable[str] | None = None, limit: int | None = None) -> List[Dict[str, Any]]:
    cases = [json.loads(line) for line in GOLDEN_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    if types:
        wanted = set(types)
        cases = [c for c in cases if c["type"] in wanted]
    return cases[:limit] if limit else cases


def matches(found_id: str, expected: str) -> bool:
    """
    A retrieved or cited id counts for an expected one when it is that node or
    sits under it: expected "903" accepts "903", "903.2" and "903.2.1.2";
    expected "table:1607.1" accepts only that table.
    """
    if expected.startswith("table:"):
        return found_id == expected
    if found_id.startswith("table:"):
        found_id = found_id.split(":", 1)[1].split("(")[0]
    return found_id == expected or found_id.startswith(expected + ".")


def first_match_rank(found_ids: List[str], expected: List[str]) -> int | None:
    """1-based position of the first retrieved id that matches any expected id."""
    for rank, found in enumerate(found_ids, start=1):
        if any(matches(found, e) for e in expected):
            return rank
    return None


def git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=BACKEND_DIR, text=True).strip()
    except Exception:
        return "unknown"


def save_result(name: str, payload: Dict[str, Any]) -> Path:
    RESULTS_DIR.mkdir(exist_ok=True)
    payload = {"name": name, "commit": git_commit(),
               "ran_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), **payload}
    path = RESULTS_DIR / f"{name}.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def percent(part: int, whole: int) -> str:
    return f"{(100 * part / whole):.0f}%" if whole else "n/a"
