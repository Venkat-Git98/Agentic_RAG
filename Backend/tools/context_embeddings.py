"""
Builds "contextual" embeddings: each passage is embedded together with a short
header saying where it sits in the code.

A passage such as "The minimum width shall be 3 feet" says nothing about courts
on its own, so a question about court width can miss it. Embedding
"Chapter 12 Interior Environment > Section 1205 Lighting > 1205.3 Courts. The
minimum width shall be 3 feet" fixes that without changing the stored text.

The new vectors go into a separate property (`embedding_ctx`) with their own
indexes, so the original embeddings stay untouched and the two can be compared
with the retrieval eval before switching.

    python -m tools.context_embeddings            # embed whatever is missing
    python -m tools.context_embeddings --redo     # re-embed everything
"""
from __future__ import annotations

import argparse
import json
import logging
import time
from typing import Any, Dict, List

from tools.code_references import chapter_of, chapter_titles
from tools.neo4j_connector import Neo4jConnector

logger = logging.getLogger(__name__)

PROPERTY = "embedding_ctx"
INDEXES = {"Passage": "passage_ctx_index", "Table": "table_ctx_index"}
BATCH_SIZE = 50
MAX_EMBED_CHARS = 6000
MAX_RETRIES = 6


def _rows(query: str, **params) -> List[Dict[str, Any]]:
    return [r.data() for r in Neo4jConnector.execute_query(query, params)]


def location(number: str, title: str, section_titles: Dict[str, str]) -> str:
    """'Chapter 16 Structural Design > Section 1607 Live Loads > 1607.12 Reduction in uniform live loads'"""
    chapter = chapter_of(number)
    parts = [f"Chapter {chapter} {chapter_titles().get(chapter, '').title()}".strip()]
    section = number.split(".")[0]
    parts.append(f"Section {section} {section_titles.get(section, '').title()}".strip())
    if section != number:
        parts.append(f"{number} {title or ''}".strip())
    return " > ".join(parts)


def passage_text(row: Dict[str, Any], section_titles: Dict[str, str]) -> str:
    return f"{location(row['number'], row['title'], section_titles)}\n{row['text']}"


def table_text(row: Dict[str, Any], section_titles: Dict[str, str]) -> str:
    def load(value):
        try:
            return json.loads(value) if isinstance(value, str) else (value or [])
        except json.JSONDecodeError:
            return []

    headers = [str(h) for h in load(row["headers"])]
    lines = [f"Table {row['table_id']} {row['title'] or ''}".strip(),
             "In " + location(row["number"], row["parent_title"], section_titles),
             " | ".join(headers)]
    for item in load(row["rows"]):
        if isinstance(item, dict):
            lines.append(" | ".join(
                ", ".join(map(str, v)) if isinstance(v, list) else str(v) for v in (item.get(h, "") for h in headers)))
    return "\n".join(lines)


def embed(texts: List[str]) -> List[List[float]]:
    import google.generativeai as genai
    from config import EMBEDDING_DIMENSIONS, EMBEDDING_MODEL

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = genai.embed_content(
                model=EMBEDDING_MODEL, content=[t[:MAX_EMBED_CHARS] for t in texts],
                task_type="RETRIEVAL_DOCUMENT", output_dimensionality=EMBEDDING_DIMENSIONS)
            vectors = response["embedding"]
            if len(vectors) != len(texts):
                raise ValueError(f"{len(vectors)} vectors for {len(texts)} texts")
            return vectors
        except Exception as e:
            if attempt == MAX_RETRIES:
                raise
            wait = min(2 ** attempt * 5, 120)
            print(f"  embedding attempt {attempt} failed ({str(e)[:120]}); retrying in {wait}s")
            time.sleep(wait)
    return []


def create_indexes() -> None:
    from config import EMBEDDING_DIMENSIONS

    for label, name in INDEXES.items():
        Neo4jConnector.execute_query(f"""
            CREATE VECTOR INDEX `{name}` IF NOT EXISTS FOR (n:{label}) ON (n.{PROPERTY})
            OPTIONS {{ indexConfig: {{ `vector.dimensions`: {EMBEDDING_DIMENSIONS},
                                      `vector.similarity_function`: 'cosine' }} }}
        """)


def pending(redo: bool) -> List[Dict[str, Any]]:
    where = "" if redo else f"AND node.{PROPERTY} IS NULL"
    section_titles = {r["number"]: r["title"] or "" for r in _rows(
        "MATCH (s:Section) RETURN s.number AS number, s.title AS title")}
    items = []
    for row in _rows(f"""
        MATCH (parent)-[:HAS_CHUNK]->(node:Passage) WHERE node.text IS NOT NULL {where}
        RETURN node.uid AS uid, node.text AS text, parent.number AS number, parent.title AS title
    """):
        items.append({"uid": row["uid"], "label": "Passage", "text": passage_text(row, section_titles)})
    for row in _rows(f"""
        MATCH (parent)-[:CONTAINS]->(node:Table) WHERE true {where}
        RETURN node.uid AS uid, node.table_id AS table_id, node.title AS title, node.headers AS headers,
               node.rows AS rows, parent.number AS number, parent.title AS parent_title
    """):
        items.append({"uid": row["uid"], "label": "Table", "text": table_text(row, section_titles)})
    return items


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--redo", action="store_true", help="re-embed nodes that already have a contextual embedding")
    args = parser.parse_args()
    logging.disable(logging.WARNING)

    create_indexes()
    items = pending(args.redo)
    print(f"{len(items)} nodes to embed")
    for start in range(0, len(items), BATCH_SIZE):
        batch = items[start:start + BATCH_SIZE]
        vectors = embed([item["text"] for item in batch])
        Neo4jConnector.execute_query(f"""
            UNWIND $rows AS row
            MATCH (n {{uid: row.uid}}) WHERE n:Passage OR n:Table
            CALL db.create.setNodeVectorProperty(n, '{PROPERTY}', row.vector)
        """, {"rows": [{"uid": item["uid"], "vector": vector} for item, vector in zip(batch, vectors)]})
        print(f"  {min(start + BATCH_SIZE, len(items))}/{len(items)}")
    print("done")


if __name__ == "__main__":
    main()
