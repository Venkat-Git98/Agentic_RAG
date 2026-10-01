"""
Resolves building-code references ("Section 1607.12", "Table 1607.1", "903.2.1")
against the Neo4j knowledge graph.

Used for two things:
  * citations: every section/table an answer mentions is looked up in the graph
    and returned with its real text, so the UI can show the source beside the claim;
  * the code browser: table of contents and section pages.

Only references that exist in the graph are returned; nothing is invented.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from tools.neo4j_connector import Neo4jConnector

logger = logging.getLogger(__name__)

SECTION_RE = re.compile(r"(?:Sections?|§)\s*(\d{3,4}(?:\.\d+)*)", re.IGNORECASE)
TABLE_RE = re.compile(r"Table\s+(\d{3,4}(?:\.\d+)*(?:\(\d+\))?)", re.IGNORECASE)
# A dotted number on its own, e.g. "(1607.12)". Only kept if that exact node exists.
BARE_RE = re.compile(r"(?<![\w.])(\d{3,4}\.\d+(?:\.\d+)*)(?![\w])")

MAX_SOURCE_CHARS = 2400
MAX_TABLE_ROWS = 60

_chapter_titles: Optional[Dict[str, str]] = None


def _records(query: str, **params) -> List[Dict[str, Any]]:
    return [r.data() for r in Neo4jConnector.execute_query(query, params)]


def natural_key(number: str) -> Tuple[int, ...]:
    return tuple(int(p) for p in re.findall(r"\d+", number or ""))


def chapter_of(number: str) -> str:
    """Section 1607.12 -> chapter 16; section 903.2 -> chapter 9."""
    head = (number or "").split(".")[0]
    return head[:-2] if len(head) > 2 else head


def chapter_titles() -> Dict[str, str]:
    global _chapter_titles
    if _chapter_titles is None:
        _chapter_titles = {r["number"]: r["title"] for r in _records(
            "MATCH (c:Chapter) RETURN c.number AS number, c.title AS title")}
    return _chapter_titles


def extract_references(text: str) -> List[Tuple[str, str, bool]]:
    """Returns ordered, de-duplicated (kind, number, explicit) tuples found in text."""
    found: List[Tuple[int, str, str, bool]] = []
    table_spans = []
    for m in TABLE_RE.finditer(text or ""):
        found.append((m.start(), "table", m.group(1), True))
        table_spans.append(m.span(1))
    explicit_spans = []
    for m in SECTION_RE.finditer(text or ""):
        found.append((m.start(), "section", m.group(1), True))
        explicit_spans.append(m.span(1))
    taken = table_spans + explicit_spans
    for m in BARE_RE.finditer(text or ""):
        if not any(s <= m.start(1) < e for s, e in taken):
            found.append((m.start(), "section", m.group(1), False))
    seen, ordered = set(), []
    for _, kind, number, explicit in sorted(found):
        if (kind, number) not in seen:
            seen.add((kind, number))
            ordered.append((kind, number, explicit))
    return ordered


def _ancestors(number: str) -> List[str]:
    parts = number.split(".")
    return [".".join(parts[:i]) for i in range(len(parts) - 1, 0, -1)]


def _node_texts(numbers: List[str]) -> Dict[str, str]:
    """Full passage text per Section/Subsection number (chunks are contiguous slices)."""
    if not numbers:
        return {}
    rows = _records("""
        MATCH (n)-[:HAS_CHUNK]->(p:Passage)
        WHERE (n:Section OR n:Subsection) AND n.number IN $numbers
        WITH n.number AS number, p ORDER BY p.chunk_index
        RETURN number, collect(p.text) AS chunks
    """, numbers=numbers)
    return {r["number"]: "".join(r["chunks"]) for r in rows}


def _parse_table(row: Dict[str, Any]) -> Dict[str, Any]:
    def load(value):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return []
        return value or []

    headers = [str(h) for h in load(row.get("headers"))]
    rows = []
    for raw in load(row.get("rows"))[:MAX_TABLE_ROWS]:
        if isinstance(raw, dict):
            cells = [raw.get(h, "") for h in headers]
        elif isinstance(raw, list):
            cells = raw
        else:
            cells = [raw]
        rows.append([", ".join(map(str, c)) if isinstance(c, list) else str(c) for c in cells])
    return {"headers": headers, "rows": rows}


def breadcrumb(number: str, section_titles: Dict[str, str]) -> str:
    chapter = chapter_of(number)
    parts = [f"Ch. {chapter} {chapter_titles().get(chapter, '').title()}".strip()]
    section = number.split(".")[0]
    if section != number or section in section_titles:
        title = section_titles.get(section, "")
        parts.append(f"§{section} {title.title()}".strip())
    return " › ".join(parts)


def resolve_references(text: str, limit: int = 12) -> List[Dict[str, Any]]:
    """
    Looks up every section/table reference in `text` and returns the ones that
    exist in the graph, with their code text. An explicit "Section 903.2.1.2"
    that has no node of its own resolves to its nearest existing parent, with
    the excerpt starting where that number appears in the parent's text.
    """
    refs = extract_references(text)
    if not refs:
        return []
    try:
        section_numbers = {n for kind, n, _ in refs if kind == "section"}
        table_ids = [n for kind, n, _ in refs if kind == "table"]
        lookup = set(section_numbers)
        for n in list(section_numbers) + table_ids:
            lookup.update(_ancestors(n))
            lookup.add(n.split(".")[0].split("(")[0])
        nodes = {r["number"]: r for r in _records("""
            MATCH (n) WHERE (n:Section OR n:Subsection) AND n.number IN $numbers
            RETURN n.number AS number, n.title AS title, labels(n)[0] AS kind
        """, numbers=sorted(lookup))}
        tables = {r["table_id"]: r for r in _records("""
            MATCH (t:Table) WHERE t.table_id IN $ids
            RETURN t.table_id AS table_id, t.title AS title, t.headers AS headers, t.rows AS rows
        """, ids=table_ids)} if table_ids else {}
        section_titles = {n: (r["title"] or "") for n, r in nodes.items() if "." not in n}

        resolved: List[Tuple[str, str, Optional[str]]] = []  # (kind, cited number, node number)
        for kind, number, explicit in refs:
            if kind == "table":
                if number in tables:
                    resolved.append(("table", number, number))
                continue
            if number in nodes:
                resolved.append(("section", number, number))
            elif explicit:
                parent = next((a for a in _ancestors(number) if a in nodes), None)
                if parent:
                    resolved.append(("section", number, parent))
        resolved = resolved[:limit]

        texts = _node_texts(sorted({node for kind, _, node in resolved if kind == "section"}))
        sources = []
        for kind, number, node_number in resolved:
            if kind == "table":
                row = tables[number]
                sources.append({
                    "id": f"table:{number}", "kind": "table", "number": number,
                    "label": f"Table {number}", "title": (row.get("title") or "").strip(),
                    "breadcrumb": breadcrumb(number.split("(")[0], section_titles),
                    "table": _parse_table(row), "exact": True,
                })
                continue
            full = texts.get(node_number, "")
            start = 0
            if node_number != number:
                found = full.find(number)
                start = max(found, 0)
            excerpt = full[start:start + MAX_SOURCE_CHARS].strip()
            if not excerpt:
                continue
            sources.append({
                "id": f"section:{number}", "kind": "section", "number": number,
                "label": f"§{number}", "title": (nodes[node_number].get("title") or "").strip(),
                "breadcrumb": breadcrumb(node_number, section_titles),
                "text": excerpt, "truncated": len(full) - start > MAX_SOURCE_CHARS,
                "exact": node_number == number, "found_in": node_number,
            })
        return sources
    except Exception as e:  # citations are an enhancement; never fail the answer over them
        logger.error(f"Could not resolve code references: {e}", exc_info=True)
        return []


def table_of_contents() -> List[Dict[str, Any]]:
    """Chapters with their sections, grouped by section-number prefix."""
    sections = _records("MATCH (s:Section) RETURN s.number AS number, s.title AS title")
    by_chapter: Dict[str, List[Dict[str, Any]]] = {}
    for s in sections:
        by_chapter.setdefault(chapter_of(s["number"]), []).append(
            {"number": s["number"], "title": (s["title"] or "").title()})
    toc = []
    for number, title in sorted(chapter_titles().items(), key=lambda kv: natural_key(kv[0])):
        toc.append({"number": number, "title": (title or "").title(),
                    "sections": sorted(by_chapter.get(number, []), key=lambda s: natural_key(s["number"]))})
    return toc


def section_page(number: str) -> Optional[Dict[str, Any]]:
    """Everything the code browser shows for one section or subsection."""
    rows = _records("""
        MATCH (n) WHERE (n:Section OR n:Subsection) AND n.number = $number
        OPTIONAL MATCH (n)-[:CONTAINS]->(c) WHERE c:Section OR c:Subsection
        WITH n, collect(DISTINCT {number: c.number, title: c.title}) AS children
        OPTIONAL MATCH (n)-[:CONTAINS]->(t:Table)
        WITH n, children, collect(DISTINCT {table_id: t.table_id, title: t.title, headers: t.headers, rows: t.rows}) AS tables
        OPTIONAL MATCH (n)-[:CONTAINS]->(m:Math)
        WITH n, children, tables, collect(DISTINCT m.latex) AS equations
        OPTIONAL MATCH (n)-[:CONTAINS]->(d:Diagram)
        WITH n, children, tables, equations, collect(DISTINCT d.description) AS diagrams
        OPTIONAL MATCH (n)-[:REFERENCES]->(s:Standard)
        RETURN n.number AS number, n.title AS title, labels(n)[0] AS kind, children, tables, equations, diagrams,
               collect(DISTINCT s.name) AS standards
    """, number=number)
    if not rows:
        return None
    row = rows[0]
    text = _node_texts([number]).get(number, "")
    section_number = number.split(".")[0]
    section_titles = {r["number"]: r["title"] or "" for r in _records(
        "MATCH (s:Section {number: $n}) RETURN s.number AS number, s.title AS title", n=section_number)}

    cites = [{"id": s["id"], "kind": s["kind"], "number": s["number"], "label": s["label"], "title": s["title"]}
             for s in resolve_references(text, limit=30)
             if s["exact"] and s["number"] != number]

    pattern = re.compile(rf"(?<![\d.]){re.escape(number)}(?!\d|\.\d)")
    cited_by, seen = [], set()
    for r in _records("""
        MATCH (x)-[:HAS_CHUNK]->(p:Passage)
        WHERE (x:Section OR x:Subsection) AND p.text CONTAINS $number AND x.number <> $number
        RETURN x.number AS number, x.title AS title, p.text AS text LIMIT 200
    """, number=number):
        if r["number"] not in seen and not r["number"].startswith(number + ".") and pattern.search(r["text"]):
            seen.add(r["number"])
            cited_by.append({"number": r["number"], "label": f"§{r['number']}", "title": r["title"] or ""})
    cited_by.sort(key=lambda c: natural_key(c["number"]))

    children = sorted([c for c in row["children"] if c.get("number")], key=lambda c: natural_key(c["number"]))
    parent = next(iter(_ancestors(number)), None)
    return {
        "number": number, "title": (row["title"] or "").strip(), "kind": row["kind"],
        "breadcrumb": breadcrumb(number, section_titles), "parent": parent,
        "text": text,
        "children": [{"number": c["number"], "title": c.get("title") or ""} for c in children],
        "tables": [{"number": t["table_id"], "title": t.get("title") or "", **_parse_table(t)}
                   for t in row["tables"] if t.get("table_id")],
        "equations": [e for e in row["equations"] if e],
        "diagrams": [d for d in row["diagrams"] if d],
        "standards": sorted(s for s in row["standards"] if s),
        "cites": cites, "cited_by": cited_by[:25],
    }
