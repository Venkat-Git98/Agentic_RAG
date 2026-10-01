"""
Checks the golden dataset against the knowledge graph.

An eval is only as good as its answer key. This confirms that every expected
section/table exists in the graph and that every expected fact really appears
in the text of an expected node, so a failing eval means the system is wrong,
not the dataset.

    python -m evals.check_dataset
"""
from __future__ import annotations

import sys

from evals.common import load_golden, matches, quiet_logging


def main() -> int:
    quiet_logging()
    from tools.neo4j_connector import Neo4jConnector

    def rows(query: str, **params):
        return [r.data() for r in Neo4jConnector.execute_query(query, params)]

    cases = load_golden()
    problems = []
    ids = [c["id"] for c in cases]
    for dup in {i for i in ids if ids.count(i) > 1}:
        problems.append(f"{dup}: duplicate id")

    for case in cases:
        if case["type"] == "not_in_graph":
            continue
        if not case["expected"]:
            problems.append(f"{case['id']}: no expected ids")
            continue
        primary = case["expected"][0]
        if primary.startswith("table:"):
            found = rows("MATCH (t:Table {table_id: $id}) RETURN t.source_markdown AS text", id=primary[6:])
            text = " ".join(r["text"] or "" for r in found)
        else:
            found = rows("""
                MATCH (n) WHERE (n:Section OR n:Subsection)
                  AND (n.number = $n OR n.number STARTS WITH $prefix)
                OPTIONAL MATCH (n)-[:HAS_CHUNK]->(p:Passage)
                OPTIONAL MATCH (n)-[:CONTAINS]->(t:Table)
                RETURN n.number AS number, collect(DISTINCT p.text) AS chunks,
                       collect(DISTINCT t.source_markdown) AS tables
            """, n=primary, prefix=primary + ".")
            exact = [r for r in found if r["number"] == primary]
            if not exact:
                found = []
            text = " ".join(" ".join(r["chunks"]) + " " + " ".join(t or "" for t in r["tables"]) for r in found)
        if not found:
            problems.append(f"{case['id']}: expected {primary} is not in the graph")
            continue
        for fact in case["facts"]:
            if fact.lower() not in text.lower():
                problems.append(f"{case['id']}: fact {fact!r} not found in the text of {primary}")

    by_type = {}
    for case in cases:
        by_type[case["type"]] = by_type.get(case["type"], 0) + 1
    print(f"{len(cases)} cases: " + ", ".join(f"{n} {t}" for t, n in sorted(by_type.items())))
    if problems:
        print(f"\n{len(problems)} problem(s):")
        for p in problems:
            print("  -", p)
        return 1
    print("Dataset is consistent with the graph.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
