"""
This module stores predefined Cypher queries for direct, efficient retrieval
of specific entities from the Neo4j database. This allows the agent to bypass
the more complex vector search and synthesis process for simple, direct questions.
"""

# Fetches a specific Subsection by its UID (e.g., "1609.1.1") and gathers all
# its immediate context, including child passages, tables, math, and diagrams.
# This is the most common direct lookup.
GET_SUBSECTION_CONTEXT_BY_ID = """
MATCH (parent:Subsection {uid: $uid})
OPTIONAL MATCH (parent)-[:HAS_CHUNK|CONTAINS]->(child)
RETURN parent, COLLECT(child) AS child_nodes
"""

# Fetches a specific Table by its UID.
GET_TABLE_BY_ID = """
MATCH (t:Table {uid: $uid})
RETURN t
"""

# Fetches a specific Diagram by its UID.
GET_DIAGRAM_BY_ID = """
MATCH (d:Diagram {uid: $uid})
RETURN d
"""

# Fetches a specific Chapter by its UID (e.g., "16") and provides its title.
# This is for high-level summary requests.
GET_CHAPTER_BY_ID = """
MATCH (c:Chapter {uid: $uid})
RETURN c.title AS title
"""

# --- NEW, MORE CONTEXT-RICH QUERIES ---

# Fetches a Chapter and lists all its Sections for a high-level overview.
GET_CHAPTER_OVERVIEW_BY_ID = """
MATCH (c:Chapter {uid: $uid})-[:CONTAINS]->(s:Section)
RETURN c.title AS chapter_title, c.number AS chapter_number,
       COLLECT({title: s.title, number: s.number, uid: s.uid}) AS sections
ORDER BY s.number
"""

# Fetches a Section and lists all its Subsections.
GET_SECTION_CONTEXT_BY_ID = """
MATCH (s:Section {uid: $uid})-[:CONTAINS]->(sub:Subsection)
RETURN s.title AS section_title, s.number AS section_number,
       COLLECT(DISTINCT {
           number: sub.number,
           title: sub.title,
           text: sub.text,
           chunks: COLLECT(DISTINCT c.text)
       }) as subsections
"""

# Fetches a Table by its common number (e.g., "1604.3") instead of its specific UID.
# It does this by matching the 'table_id' property, which often contains the common name.
# Using CONTAINS for a more robust match against potential whitespace issues.
GET_TABLE_BY_COMMON_ID = """
MATCH (t:Table) WHERE t.table_id CONTAINS $uid
RETURN t
"""

GET_FULL_SUBSECTION_HIERARCHY = """
// Find the starting subsection node by its number (e.g., "1607.12")
MATCH (start_node:Subsection {number: $uid})
// Traverse all child relationships recursively to find all descendant nodes
// This includes nested Subsections, Passages, Tables, Math, etc.
CALL {
    WITH start_node
    MATCH (start_node)-[:HAS_CHUNK|CONTAINS*0..]->(descendant)
    RETURN COLLECT(DISTINCT descendant) AS all_nodes
}
// Return the parent and the collected list of all its children and their children
RETURN start_node as parent, all_nodes as child_nodes
"""

GET_FULL_SECTION_HIERARCHY = """
// Find the starting Section node by its number (e.g., "1607")
MATCH (start_node:Section {number: $uid})
// Find all descendant nodes (subsections and their children)
CALL {
    WITH start_node
    MATCH (start_node)-[:HAS_CHUNK|CONTAINS*0..]->(descendant)
    RETURN COLLECT(DISTINCT descendant) AS all_nodes
}
// Return the parent section and all its descendants
RETURN start_node as parent, all_nodes as child_nodes
""" 