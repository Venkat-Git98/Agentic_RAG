"""
Hybrid retrieval over the building-code knowledge graph.

One function, `search`, replaces the old vector -> keyword -> lookup cascade.
It runs every signal for a question and merges the rankings:

  * explicit references: "Section 1607.12" or "Table 1607.1" in the question is
    looked up directly;
  * vector search over passages, tables and diagrams, with the question
    embedded as a query (RETRIEVAL_QUERY), not as a document;
  * full-text search over passage text and section titles, used when vector
    search is unavailable (the eval showed it lowers accuracy as an extra vote).

The rankings are merged with weighted reciprocal rank fusion, grouped by the section the
passages belong to, and each hit is returned with its own text, tables and
equations so the model sees real code text with the section number attached.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from tools.code_references import _ancestors, breadcrumb, extract_references
from tools.neo4j_connector import Neo4jConnector

logger = logging.getLogger(__name__)

RRF_K = 60                 # standard constant: damps the gap between rank 1 and rank 2
CANDIDATES = 20            # how many results each signal contributes
EXPLICIT_BONUS = 1.0       # a section named in the question always ranks first
MAX_SECTION_CHARS = 5000   # longer sections are cut down to the chunks that matched
MAX_TABLE_CHARS = 3500
VECTOR_INDEXES = ("passage", "table", "diagram")
# Two sets of embeddings live in the graph: "plain" (bare passage text) and
# "context" (passage text with its chapter/section header, see tools/context_embeddings.py).
INDEX_SETS = {
    "plain": {"passage": "passage_embedding_index", "table": "table_embedding_index", "diagram": "diagram_embedding_index"},
    "context": {"passage": "passage_ctx_index", "table": "table_ctx_index", "diagram": "diagram_embedding_index"},
}
# How much each signal's vote counts in the fusion. Set from the retrieval eval:
# on the golden set, adding keyword votes to the vector ranking lowered hit@1
# (94% -> 78%), so full-text is the fallback when vector search is unavailable,
# not a vote. Re-run `python -m evals.retrieval_eval --variant all` before changing.
WEIGHTS = {"vector": 1.0, "text": 0.0, "title": 0.0}
FALLBACK_WEIGHTS = {"text": 1.0, "title": 0.5}

STOPWORDS = set("""
a about above after all also an and any are as at be been before below between both but by can could
do does each for from had has have how if in into is it its may more most must need needed no not of
on only or other out over per shall should so some such than that the their them then there these
they this those to under up use used was what when where which who why will with within would
apply applies applied require required requirement requirements code building virginia section say
says tell show explain give many much kind
""".split())


@dataclass
class Hit:
    id: str                      # "1607.12" for a section, "table:1607.1" for a table
    kind: str                    # "section" or "table"
    number: str
    score: float = 0.0
    via: Set[str] = field(default_factory=set)   # which signals found it
    title: str = ""
    breadcrumb: str = ""
    text: str = ""
    tables: List[Dict[str, str]] = field(default_factory=list)
    equations: List[str] = field(default_factory=list)
    children: List[str] = field(default_factory=list)

    @property
    def label(self) -> str:
        return f"Table {self.number}" if self.kind == "table" else f"Section {self.number}"


def _rows(query: str, **params) -> List[Dict[str, Any]]:
    return [r.data() for r in Neo4jConnector.execute_query(query, params)]


def embed_query(text: str, task_type: str = "RETRIEVAL_QUERY") -> List[float]:
    import google.generativeai as genai
    from config import EMBEDDING_DIMENSIONS, EMBEDDING_MODEL, GOOGLE_API_KEY

    genai.configure(api_key=GOOGLE_API_KEY)
    response = genai.embed_content(
        model=EMBEDDING_MODEL, content=text, task_type=task_type,
        output_dimensionality=EMBEDDING_DIMENSIONS)
    return response["embedding"]


def keywords(query: str) -> List[str]:
    """The words worth matching: no stopwords, no section numbers, no duplicates."""
    words, seen = [], set()
    for word in re.findall(r"[A-Za-z][A-Za-z0-9\-]+", query):
        low = word.lower()
        if len(low) > 2 and low not in STOPWORDS and low not in seen:
            seen.add(low)
            words.append(low)
    return words


def _lucene(words: Sequence[str]) -> str:
    # Hyphenated terms are quoted so Lucene treats them as a phrase, not an operator.
    return " OR ".join(f'"{w}"' if "-" in w else w for w in words)


# --- the individual signals: each returns a ranked list of (hit id, chunk index) ---

def _explicit_signal(query: str) -> List[Tuple[str, Optional[int]]]:
    refs = extract_references(query)
    if not refs:
        return []
    sections = [n for kind, n, _ in refs if kind == "section"]
    tables = [n for kind, n, _ in refs if kind == "table"]
    lookup = set(sections)
    for n in sections:
        lookup.update(_ancestors(n))
    existing = {r["number"] for r in _rows(
        "MATCH (n) WHERE (n:Section OR n:Subsection) AND n.number IN $numbers RETURN n.number AS number",
        numbers=sorted(lookup))} if lookup else set()
    existing_tables = {r["id"] for r in _rows(
        "MATCH (t:Table) WHERE t.table_id IN $ids RETURN t.table_id AS id", ids=tables)} if tables else set()
    ranked: List[Tuple[str, Optional[int]]] = []
    for kind, number, _ in refs:
        if kind == "table":
            if number in existing_tables:
                ranked.append((f"table:{number}", None))
            continue
        target = number if number in existing else next((a for a in _ancestors(number) if a in existing), None)
        if target:
            ranked.append((target, None))
    return ranked


def _vector_signal(embedding: List[float], indexes: Iterable[str],
                   index_set: Optional[str] = None) -> List[Tuple[str, Optional[int]]]:
    from config import VECTOR_INDEX_SET

    names = INDEX_SETS[index_set or VECTOR_INDEX_SET]
    parts = []
    if "passage" in indexes:
        parts.append("""
            CALL db.index.vector.queryNodes($passage_index, $n, $embedding) YIELD node, score
            RETURN node.parent_uid AS id, node.chunk_index AS chunk, score""")
    if "table" in indexes:
        parts.append("""
            CALL db.index.vector.queryNodes($table_index, $n, $embedding) YIELD node, score
            RETURN 'table:' + node.table_id AS id, null AS chunk, score""")
    if "diagram" in indexes:
        parts.append("""
            CALL db.index.vector.queryNodes($diagram_index, $n, $embedding) YIELD node, score
            MATCH (parent)-[:CONTAINS]->(node)
            RETURN parent.number AS id, null AS chunk, score""")
    rows = _rows(" UNION ALL ".join(parts), n=CANDIDATES, embedding=embedding,
                 passage_index=names["passage"], table_index=names["table"], diagram_index=names["diagram"])
    rows.sort(key=lambda r: r["score"], reverse=True)
    return [(r["id"], r["chunk"]) for r in rows if r["id"]]


def _passage_text_signal(words: Sequence[str]) -> List[Tuple[str, Optional[int]]]:
    if not words:
        return []
    rows = _rows("""
        CALL db.index.fulltext.queryNodes('passage_content_idx', $q, {limit: $n}) YIELD node, score
        RETURN node.parent_uid AS id, node.chunk_index AS chunk, score ORDER BY score DESC
    """, q=_lucene(words), n=CANDIDATES)
    return [(r["id"], r["chunk"]) for r in rows if r["id"]]


def _title_signal(words: Sequence[str]) -> List[Tuple[str, Optional[int]]]:
    if not words:
        return []
    rows = _rows("""
        CALL db.index.fulltext.queryNodes('knowledge_base_text_idx', $q, {limit: $n}) YIELD node, score
        WHERE node:Section OR node:Subsection
        RETURN node.number AS id, score ORDER BY score DESC
    """, q=" OR ".join(f"title:{w}" for w in _lucene(words).split(" OR ")), n=CANDIDATES)
    return [(r["id"], None) for r in rows if r["id"]]


# --- fusion and hydration ---

def _fuse(signals: Dict[str, List[Tuple[str, Optional[int]]]],
          weights: Dict[str, float]) -> Tuple[List[Hit], Dict[str, Set[int]]]:
    """
    Weighted reciprocal rank fusion. Each signal votes weight / (RRF_K + rank)
    for what it found, so something ranked well by several signals beats something ranked
    first by only one. Several passages of one section count once, at the
    position of the best one.
    """
    hits: Dict[str, Hit] = {}
    chunks: Dict[str, Set[int]] = {}
    for name, ranked in signals.items():
        seen: Set[str] = set()
        rank = 0
        for hit_id, chunk in ranked:
            if chunk is not None:
                chunks.setdefault(hit_id, set()).add(int(chunk))
            if hit_id in seen:
                continue
            seen.add(hit_id)
            rank += 1
            kind = "table" if hit_id.startswith("table:") else "section"
            hit = hits.setdefault(hit_id, Hit(id=hit_id, kind=kind, number=hit_id.split(":", 1)[-1]))
            hit.score += EXPLICIT_BONUS + 1.0 / rank if name == "reference" else weights.get(name, 1.0) / (RRF_K + rank)
            hit.via.add(name)
    return sorted(hits.values(), key=lambda h: h.score, reverse=True), chunks


def _section_text(passages: List[Dict[str, Any]], matched: Set[int]) -> str:
    """Whole text for a normal section; for a very long one, the chunks that matched plus the next one."""
    passages = sorted(passages, key=lambda p: int(p["chunk"]))
    full = "".join(p["text"] or "" for p in passages)
    if len(full) <= MAX_SECTION_CHARS:
        return full
    wanted = sorted(matched | {i + 1 for i in matched}) or [0]
    by_index = {int(p["chunk"]): p["text"] or "" for p in passages}
    parts, size, previous = [], 0, None
    for index in wanted:
        text = by_index.get(index)
        if text is None or size + len(text) > MAX_SECTION_CHARS:
            continue
        parts.append(("" if previous is None or index == previous + 1 else "\n[...]\n") + text)
        size += len(text)
        previous = index
    return "".join(parts) or full[:MAX_SECTION_CHARS]


def _hydrate(hits: List[Hit], chunks: Dict[str, Set[int]]) -> List[Hit]:
    section_numbers = [h.number for h in hits if h.kind == "section"]
    table_ids = [h.number for h in hits if h.kind == "table"]
    sections = {r["number"]: r for r in _rows("""
        MATCH (n) WHERE (n:Section OR n:Subsection) AND n.number IN $numbers
        OPTIONAL MATCH (n)-[:HAS_CHUNK]->(p:Passage)
        WITH n, collect({chunk: p.chunk_index, text: p.text}) AS passages
        OPTIONAL MATCH (n)-[:CONTAINS]->(t:Table)
        WITH n, passages, collect(DISTINCT {id: t.table_id, title: t.title, markdown: t.source_markdown}) AS tables
        OPTIONAL MATCH (n)-[:CONTAINS]->(m:Math)
        WITH n, passages, tables, collect(DISTINCT m.latex) AS equations
        OPTIONAL MATCH (n)-[:CONTAINS]->(c) WHERE c:Section OR c:Subsection
        RETURN n.number AS number, n.title AS title, passages, tables, equations,
               collect(DISTINCT c.number + ' ' + coalesce(c.title, '')) AS children
    """, numbers=section_numbers)} if section_numbers else {}
    tables = {r["id"]: r for r in _rows("""
        MATCH (t:Table) WHERE t.table_id IN $ids
        RETURN t.table_id AS id, t.title AS title, t.source_markdown AS markdown
    """, ids=table_ids)} if table_ids else {}
    top_sections = {n.split(".")[0].split("(")[0] for n in section_numbers + table_ids}
    section_titles = {r["number"]: r["title"] or "" for r in _rows(
        "MATCH (s:Section) WHERE s.number IN $numbers RETURN s.number AS number, s.title AS title",
        numbers=sorted(top_sections))}

    hydrated = []
    for hit in hits:
        if hit.kind == "table":
            row = tables.get(hit.number)
            if not row:
                continue
            hit.title = (row["title"] or "").strip()
            hit.text = (row["markdown"] or "")[:MAX_TABLE_CHARS]
            hit.breadcrumb = breadcrumb(hit.number.split("(")[0], section_titles)
        else:
            row = sections.get(hit.number)
            if not row:
                continue
            hit.title = (row["title"] or "").strip()
            hit.breadcrumb = breadcrumb(hit.number, section_titles)
            hit.text = _section_text([p for p in row["passages"] if p.get("text")], chunks.get(hit.id, set()))
            hit.tables = [{"id": t["id"], "title": (t["title"] or "").strip(),
                           "markdown": (t["markdown"] or "")[:MAX_TABLE_CHARS]}
                          for t in row["tables"] if t.get("id")]
            hit.equations = [e for e in row["equations"] if e]
            hit.children = sorted(c.strip() for c in row["children"] if c)
            if not (hit.text or hit.tables or hit.equations or hit.children):
                continue
        hydrated.append(hit)
    return hydrated


def search(
    query: str,
    k: int = 6,
    *,
    task_type: str = "RETRIEVAL_QUERY",
    use_reference: bool = True,
    use_vector: bool = True,
    use_fulltext: bool = True,
    indexes: Iterable[str] = VECTOR_INDEXES,
    embedding: Optional[List[float]] = None,
    weights: Optional[Dict[str, float]] = None,
    index_set: Optional[str] = None,
    hydrate: bool = True,
) -> List[Hit]:
    """
    Returns the top `k` sections/tables for a question, best first.

    The keyword arguments switch individual signals off. The app always uses
    the defaults; the evals use the switches to measure what each signal adds.
    """
    signals: Dict[str, List[Tuple[str, Optional[int]]]] = {}
    if use_reference:
        signals["reference"] = _explicit_signal(query)
    if use_vector:
        try:
            signals["vector"] = _vector_signal(embedding or embed_query(query, task_type), tuple(indexes), index_set)
        except Exception as e:  # an embedding outage should not take keyword search down with it
            logger.error(f"Vector search failed: {e}")
    weights = dict(weights or WEIGHTS)
    if not signals.get("vector"):
        weights.update(FALLBACK_WEIGHTS)
    if use_fulltext and (weights.get("text") or weights.get("title")):
        words = keywords(query)
        try:
            signals["text"] = _passage_text_signal(words)
            signals["title"] = _title_signal(words)
        except Exception as e:
            logger.error(f"Full-text search failed: {e}")
    hits, chunks = _fuse(signals, weights)
    hits = hits[:k]
    return _hydrate(hits, chunks) if hydrate else hits


def format_context(hits: List[Hit]) -> str:
    """Plain text for the model: every block starts with the section it came from."""
    blocks = []
    for hit in hits:
        heading = f"[{hit.label}" + (f": {hit.title}" if hit.title else "") + "]"
        lines = [heading + (f" ({hit.breadcrumb})" if hit.breadcrumb else "")]
        if hit.text:
            lines.append(hit.text.strip())
        elif hit.children:
            lines.append("This section is divided into: " + "; ".join(hit.children[:25]))
        for table in hit.tables:
            lines.append(f"Table {table['id']}" + (f": {table['title']}" if table["title"] else ""))
            lines.append(table["markdown"])
        if hit.equations:
            lines.append("Equations: " + " ; ".join(hit.equations))
        blocks.append("\n".join(lines))
    return "\n\n---\n\n".join(blocks)
