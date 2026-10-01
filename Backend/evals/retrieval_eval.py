"""
Retrieval eval: does the right section come back, and how high?

For each golden question it runs the retriever and looks for the first result
that matches an expected section or table. No language model is involved, so it
is fast, free and repeatable, which makes it the eval to run on every change.

Metrics
  hit@k  share of questions whose expected section is in the top k results
  MRR    mean reciprocal rank: 1 for rank 1, 1/2 for rank 2, ... 0 for a miss

    python -m evals.retrieval_eval                    # the retriever the app uses
    python -m evals.retrieval_eval --variant all      # compare every variant
    python -m evals.retrieval_eval --min-hit3 0.9     # exit 1 below the bar (for CI)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from typing import Any, Dict, List

from evals.common import EVALS_DIR, first_match_rank, load_golden, quiet_logging, save_result

K = 10

# Each variant is the same `search` function with signals switched on or off,
# so a difference in score is caused by exactly one change.
VARIANTS: Dict[str, Dict[str, Any]] = {
    # what the app did before: question embedded as a document, passages only
    "legacy": dict(task_type="RETRIEVAL_DOCUMENT", use_reference=False, use_fulltext=False, indexes=("passage",), index_set="plain"),
    # + embed the question as a query
    "query-embed": dict(use_reference=False, use_fulltext=False, indexes=("passage",), index_set="plain"),
    # + also search the table and diagram indexes
    "all-indexes": dict(use_reference=False, use_fulltext=False, index_set="plain"),
    # full-text only, to see what keywords alone can do (also the fallback path)
    "fulltext": dict(use_reference=False, use_vector=False),
    # experiment: vector and full-text rankings fused with equal votes
    "fused": dict(use_reference=False, weights={"vector": 1.0, "text": 1.0, "title": 1.0}, index_set="plain"),
    # all vector indexes + sections named in the question, on the plain embeddings
    "hybrid-plain": dict(index_set="plain"),
    # same, on embeddings that include each passage's chapter/section header
    "hybrid-context": dict(index_set="context"),
    # whatever the app is configured to use (VECTOR_INDEX_SET)
    "app": dict(),
}

CACHE_PATH = EVALS_DIR / ".cache" / "query_embeddings.json"


class EmbeddingCache:
    """Question embeddings never change, so keep them on disk between runs."""

    def __init__(self) -> None:
        self.data = json.loads(CACHE_PATH.read_text()) if CACHE_PATH.exists() else {}

    def get(self, question: str, task_type: str) -> List[float]:
        from config import EMBEDDING_DIMENSIONS, EMBEDDING_MODEL
        from tools.retriever import embed_query

        key = hashlib.sha1(f"{EMBEDDING_MODEL}|{EMBEDDING_DIMENSIONS}|{task_type}|{question}".encode()).hexdigest()
        if key not in self.data:
            self.data[key] = embed_query(question, task_type)
            CACHE_PATH.parent.mkdir(exist_ok=True)
            CACHE_PATH.write_text(json.dumps(self.data))
        return self.data[key]


def run_variant(name: str, cases: List[Dict[str, Any]], cache: EmbeddingCache) -> Dict[str, Any]:
    from tools.retriever import search

    options = VARIANTS[name]
    rows = []
    started = time.time()
    for case in cases:
        embedding = None
        if options.get("use_vector", True):
            embedding = cache.get(case["question"], options.get("task_type", "RETRIEVAL_QUERY"))
        hits = search(case["question"], k=K, embedding=embedding, hydrate=False, **options)
        found = [h.id for h in hits]
        rows.append({"id": case["id"], "type": case["type"], "question": case["question"],
                     "expected": case["expected"], "rank": first_match_rank(found, case["expected"]),
                     "top": found[:5]})
    return {"variant": name, "seconds": round(time.time() - started, 1), **summarize(rows), "cases": rows}


def summarize(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    def metrics(subset: List[Dict[str, Any]]) -> Dict[str, Any]:
        n = len(subset)
        ranks = [r["rank"] for r in subset]
        return {
            "n": n,
            "hit@1": round(sum(1 for r in ranks if r and r <= 1) / n, 3),
            "hit@3": round(sum(1 for r in ranks if r and r <= 3) / n, 3),
            "hit@5": round(sum(1 for r in ranks if r and r <= 5) / n, 3),
            "mrr": round(sum(1 / r for r in ranks if r) / n, 3),
        }

    types = sorted({r["type"] for r in rows})
    return {"overall": metrics(rows), "by_type": {t: metrics([r for r in rows if r["type"] == t]) for t in types}}


def print_table(results: List[Dict[str, Any]]) -> None:
    print(f"\n{'variant':<14}{'n':>4}{'hit@1':>8}{'hit@3':>8}{'hit@5':>8}{'MRR':>8}")
    for result in results:
        m = result["overall"]
        print(f"{result['variant']:<14}{m['n']:>4}{m['hit@1']:>8.0%}{m['hit@3']:>8.0%}{m['hit@5']:>8.0%}{m['mrr']:>8.2f}")
    last = results[-1]
    print(f"\n{last['variant']} by question type:")
    for kind, m in last["by_type"].items():
        print(f"  {kind:<12}{m['n']:>4}{m['hit@1']:>8.0%}{m['hit@3']:>8.0%}{m['hit@5']:>8.0%}{m['mrr']:>8.2f}")
    misses = [c for c in last["cases"] if not c["rank"] or c["rank"] > 3]
    if misses:
        print(f"\n{last['variant']}: not in the top 3 ({len(misses)}):")
        for c in misses:
            print(f"  {c['id']:<28} rank={c['rank']}  expected={c['expected'][0]}  got={c['top'][:3]}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--variant", default="app", choices=[*VARIANTS, "all"])
    parser.add_argument("--min-hit3", type=float, help="fail if hit@3 of the last variant is below this")
    parser.add_argument("--min-mrr", type=float, help="fail if MRR of the last variant is below this")
    parser.add_argument("--tag", default="", help="suffix for the result file, e.g. 'before-reembed'")
    args = parser.parse_args()

    quiet_logging()
    # Questions about parts of the code that are not in the graph have no right answer to retrieve.
    cases = [c for c in load_golden() if c["type"] != "not_in_graph"]
    cache = EmbeddingCache()
    names = list(VARIANTS) if args.variant == "all" else [args.variant]
    results = [run_variant(name, cases, cache) for name in names]
    print_table(results)
    for result in results:
        save_result(f"retrieval-{result['variant']}" + (f"-{args.tag}" if args.tag else ""), result)

    final = results[-1]["overall"]
    failed = []
    if args.min_hit3 is not None and final["hit@3"] < args.min_hit3:
        failed.append(f"hit@3 {final['hit@3']:.2f} < {args.min_hit3}")
    if args.min_mrr is not None and final["mrr"] < args.min_mrr:
        failed.append(f"MRR {final['mrr']:.2f} < {args.min_mrr}")
    if failed:
        print("\nFAILED: " + "; ".join(failed))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
