"""
End-to-end eval: ask the running app real questions and grade the answers.

The retrieval eval checks one component. This one checks what a user sees, by
calling the same /api/chat endpoint the website uses (with the answer cache
turned off, so every run measures the live pipeline).

Graded per answer
  answered       an answer came back without an error
  citation hit   the answer cites an expected section/table that exists in the graph
  fact recall    share of the expected facts (numbers, standards) present in the answer
  web fallback   the code graph was not enough and a web search was used
  seconds        time to the full answer
  judge (opt.)   a model compares the answer with the real code text: 1 (wrong) to 5 (correct)

    python -m evals.e2e_eval --sample 10                         # quick check against localhost:8030
    python -m evals.e2e_eval --base-url https://agenticrag-production.up.railway.app --sample 10
    python -m evals.e2e_eval --judge                             # full set with the model judge
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List

import requests

from evals.common import load_golden, matches, quiet_logging, save_result

DEFAULT_BASE_URL = "http://localhost:8030"
TIMEOUT_SECONDS = 300

JUDGE_PROMPT = """You are grading an answer about the Virginia building code.

Question: {question}

Code text that contains the correct answer:
---
{reference}
---

Answer to grade:
---
{answer}
---

Grade only against the code text above.
5 = fully correct and complete
4 = correct, minor omission
3 = partly correct, or correct but vague
2 = mostly wrong or misses the point
1 = wrong, or contradicts the code text

Reply with JSON only: {{"score": <1-5>, "reason": "<one sentence>"}}"""


def ask(base_url: str, question: str) -> Dict[str, Any]:
    """Sends one question to /api/chat and collects the streamed parts."""
    started = time.time()
    out: Dict[str, Any] = {"text": "", "sources": [], "meta": {}, "error": None}
    try:
        with requests.post(
            f"{base_url.rstrip('/')}/api/chat",
            json={"messages": [{"role": "user", "parts": [{"type": "text", "text": question}]}],
                  "no_cache": True, "source": "eval"},
            stream=True, timeout=TIMEOUT_SECONDS,
        ) as response:
            response.raise_for_status()
            for raw in response.iter_lines(decode_unicode=True):
                if not raw or not raw.startswith("data: ") or raw == "data: [DONE]":
                    continue
                part = json.loads(raw[6:])
                kind = part.get("type")
                if kind == "text-delta":
                    out["text"] += part.get("delta", "")
                elif kind == "data-sources":
                    out["sources"] = part["data"].get("sources", [])
                elif kind == "data-meta":
                    out["meta"] = part.get("data", {})
                elif kind == "error":
                    out["error"] = part.get("errorText")
    except Exception as e:
        out["error"] = f"{type(e).__name__}: {e}"
    out["seconds"] = round(time.time() - started, 1)
    return out


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().replace(",", ""))


def cited_ids(sources: List[Dict[str, Any]]) -> List[str]:
    ids = []
    for s in sources:
        ids.append(f"table:{s['number']}" if s.get("kind") == "table" else s.get("number", ""))
    return ids


def grade(case: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
    answer = normalize(result["text"])
    facts = case["facts"]
    found = [f for f in facts if normalize(f) in answer]
    cited = cited_ids(result["sources"])
    return {
        "id": case["id"], "type": case["type"], "question": case["question"],
        "answered": bool(result["text"].strip()) and not result["error"],
        "error": result["error"],
        "citation_hit": any(matches(c, e) for c in cited for e in case["expected"]) if case["expected"] else None,
        "fact_recall": round(len(found) / len(facts), 2) if facts else None,
        "missing_facts": [f for f in facts if f not in found],
        "web_used": bool(result["meta"].get("web_used")),
        "route": result["meta"].get("route"),
        "seconds": result["seconds"],
        "cited": cited[:8],
        "answer": result["text"],
    }


def reference_text(expected: List[str]) -> str:
    """The real code text for the first expected section/table, for the judge."""
    from tools.retriever import Hit, _hydrate, format_context

    target = expected[0]
    kind = "table" if target.startswith("table:") else "section"
    hits = _hydrate([Hit(id=target, kind=kind, number=target.split(":", 1)[-1])], {})
    return format_context(hits)[:6000]


def judge(row: Dict[str, Any], case: Dict[str, Any]) -> Dict[str, Any]:
    import google.generativeai as genai
    from config import GOOGLE_API_KEY, TIER_2_MODEL_NAME

    genai.configure(api_key=GOOGLE_API_KEY)
    prompt = JUDGE_PROMPT.format(question=case["question"], reference=reference_text(case["expected"]),
                                 answer=row["answer"][:6000])
    try:
        model = genai.GenerativeModel(TIER_2_MODEL_NAME, generation_config={"temperature": 0})
        verdict = json.loads(re.search(r"\{.*\}", model.generate_content(prompt).text, re.S).group(0))
        return {"judge_score": int(verdict["score"]), "judge_reason": verdict.get("reason", "")}
    except Exception as e:
        return {"judge_score": None, "judge_reason": f"judge failed: {e}"}


def mean(values: List[float]) -> float | None:
    values = [v for v in values if v is not None]
    return round(sum(values) / len(values), 3) if values else None


def summarize(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    in_graph = [r for r in rows if r["type"] != "not_in_graph"]
    gaps = [r for r in rows if r["type"] == "not_in_graph"]
    seconds = sorted(r["seconds"] for r in rows)
    return {
        "n": len(rows),
        "answered": mean([float(r["answered"]) for r in rows]),
        "citation_hit": mean([float(r["citation_hit"]) for r in in_graph if r["citation_hit"] is not None]),
        "fact_recall": mean([r["fact_recall"] for r in in_graph]),
        "web_fallback_in_graph": mean([float(r["web_used"]) for r in in_graph]),
        "web_fallback_not_in_graph": mean([float(r["web_used"]) for r in gaps]),
        "judge_score": mean([r.get("judge_score") for r in in_graph]),
        "seconds_p50": seconds[len(seconds) // 2] if seconds else None,
        "seconds_max": seconds[-1] if seconds else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--sample", type=int, help="run an evenly spaced sample of this many cases")
    parser.add_argument("--ids", nargs="*", help="run only these case ids")
    parser.add_argument("--concurrency", type=int, default=2)
    parser.add_argument("--judge", action="store_true", help="also grade answers with a model against the code text")
    parser.add_argument("--tag", default="", help="suffix for the result file")
    parser.add_argument("--min-citation-hit", type=float)
    parser.add_argument("--min-fact-recall", type=float)
    args = parser.parse_args()

    quiet_logging()
    cases = load_golden()
    if args.ids:
        cases = [c for c in cases if c["id"] in set(args.ids)]
    elif args.sample and args.sample < len(cases):
        step = len(cases) / args.sample
        cases = [cases[int(i * step)] for i in range(args.sample)]

    print(f"Asking {len(cases)} questions at {args.base_url} ...")
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        results = list(pool.map(lambda c: ask(args.base_url, c["question"]), cases))
    rows = [grade(case, result) for case, result in zip(cases, results)]
    if args.judge:
        for row, case in zip(rows, cases):
            if case["type"] != "not_in_graph" and row["answered"]:
                row.update(judge(row, case))

    print(f"\n{'case':<28}{'ok':>4}{'cite':>6}{'facts':>7}{'web':>5}{'judge':>7}{'sec':>7}  route")
    for r in rows:
        show = lambda v, fmt="{}": "-" if v is None else fmt.format(v)
        print(f"{r['id']:<28}{'y' if r['answered'] else 'N':>4}{show(r['citation_hit'] and 'y' or (None if r['citation_hit'] is None else 'N')):>6}"
              f"{show(r['fact_recall']):>7}{'y' if r['web_used'] else '':>5}{show(r.get('judge_score')):>7}{r['seconds']:>7}  {r['route']}")
        if r["error"]:
            print(f"    error: {r['error']}")
    summary = summarize(rows)
    print("\nSummary")
    for key, value in summary.items():
        print(f"  {key:<28}{value}")

    name = "e2e" + (f"-{args.tag}" if args.tag else "")
    path = save_result(name, {"base_url": args.base_url, "summary": summary, "cases": rows})
    print(f"\nSaved {path}")

    failed = []
    if args.min_citation_hit is not None and (summary["citation_hit"] or 0) < args.min_citation_hit:
        failed.append(f"citation_hit {summary['citation_hit']} < {args.min_citation_hit}")
    if args.min_fact_recall is not None and (summary["fact_recall"] or 0) < args.min_fact_recall:
        failed.append(f"fact_recall {summary['fact_recall']} < {args.min_fact_recall}")
    if failed:
        print("FAILED: " + "; ".join(failed))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
