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
WITH c, s ORDER BY s.number
RETURN c.title AS chapter_title, c.number AS chapter_number,
       COLLECT({title: s.title, number: s.number, uid: s.uid}) AS sections
"""

# Fetches a Section and lists all its Subsections.
GET_SECTION_CONTEXT_BY_ID = """
MATCH (s:Section {uid: $uid})-[:CONTAINS]->(sub:Subsection)
// For each subsection, find its child text chunks
OPTIONAL MATCH (sub)-[:HAS_CHUNK]->(c:Passage)
WITH s, sub, COLLECT(DISTINCT c.text) AS chunks
RETURN s.title AS section_title, s.number AS section_number,
       COLLECT({ \
           number: sub.number,
           title: sub.title,
           text: sub.text, \
           chunks: chunks\
       }) as subsections
"""

# Fetches a Table by its common number (e.g., "1604.3") instead of its specific UID.
# It does this by matching the 'table_id' property, which often contains the common name.
# Using CONTAINS for a more robust match against potential whitespace issues.
GET_TABLE_BY_COMMON_ID = """
MATCH (t:Table) WHERE t.table_id CONTAINS $uid
CALL {
    WITH t
    MATCH (t)-[:HAS_CHUNK|CONTAINS*0..]->(descendant)
    RETURN COLLECT(DISTINCT descendant) AS all_nodes
}
RETURN t as parent, all_nodes as child_nodes
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

# --- ENHANCED MATHEMATICAL CONTENT QUERIES ---

# Enhanced subsection query that explicitly includes Math, Diagram, and Table nodes
GET_ENHANCED_SUBSECTION_CONTEXT = """
MATCH (parent:Subsection {uid: $uid})

// Get all regular content
OPTIONAL MATCH (parent)-[:HAS_CHUNK|CONTAINS]->(content)

// Explicitly get Math nodes
OPTIONAL MATCH (parent)-[:CONTAINS]->(math:Math)

// Explicitly get Diagram nodes  
OPTIONAL MATCH (parent)-[:CONTAINS]->(diagram:Diagram)

// Explicitly get Table nodes
OPTIONAL MATCH (parent)-[:CONTAINS]->(table:Table)

// Also check for referenced Math/Tables from other subsections
OPTIONAL MATCH (parent)-[:REFERENCES]->(ref_math:Math)
OPTIONAL MATCH (parent)-[:REFERENCES]->(ref_table:Table)

RETURN 
    parent,
    COLLECT(DISTINCT content) AS content_nodes,
    COLLECT(DISTINCT math) AS math_nodes,
    COLLECT(DISTINCT diagram) AS diagram_nodes,
    COLLECT(DISTINCT table) AS table_nodes,
    COLLECT(DISTINCT ref_math) AS referenced_math,
    COLLECT(DISTINCT ref_table) AS referenced_tables
"""

# Get all equations from a specific chapter
GET_CHAPTER_EQUATIONS = """
MATCH (c:Chapter {number: $chapter_number})
MATCH (c)-[:CONTAINS*1..]->(math:Math)
RETURN 
    math.uid AS uid,
    math.latex AS latex,
    math.uid AS equation_id
ORDER BY math.uid
"""

# Get all equations from a specific subsection or section
GET_SECTION_EQUATIONS = """
MATCH (s {number: $section_number})
WHERE s:Section OR s:Subsection
MATCH (s)-[:CONTAINS*0..]->(math:Math)
RETURN 
    math.uid AS uid,
    math.latex AS latex,
    math.uid AS equation_id
ORDER BY math.uid
"""

# Find math nodes by pattern matching on UIDs
GET_MATH_BY_PATTERN = """
MATCH (math:Math)
WHERE math.uid CONTAINS $pattern
RETURN 
    math.uid AS uid,
    math.latex AS latex,
    math.uid AS equation_id
ORDER BY math.uid
LIMIT 10
"""

# Get all tables from a specific chapter  
GET_CHAPTER_TABLES = """
MATCH (c:Chapter {number: $chapter_number})
MATCH (c)-[:CONTAINS*1..]->(table:Table)
RETURN 
    table.uid AS uid,
    table.title AS title,
    table.table_id AS table_id,
    table.headers AS headers,
    table.rows AS rows
ORDER BY table.uid
"""

# Get all diagrams from a specific chapter
GET_CHAPTER_DIAGRAMS = """
MATCH (c:Chapter {number: $chapter_number})
MATCH (c)-[:CONTAINS*1..]->(diagram:Diagram)
RETURN 
    diagram.uid AS uid,
    diagram.path AS path,
    diagram.description AS description
ORDER BY diagram.uid
"""

# Enhanced query that gets context with explicit mathematical content expansion
GET_EXPANDED_MATHEMATICAL_CONTEXT = """
// Find the main node (could be Section or Subsection)
MATCH (main_node) WHERE main_node.uid = $uid

// Get regular content
CALL {
    WITH main_node
    MATCH (main_node)-[:HAS_CHUNK|CONTAINS*0..]->(content)
    WHERE NOT content:Math AND NOT content:Diagram AND NOT content:Table
    RETURN COLLECT(DISTINCT content) AS regular_content
}

// Get all mathematical content
CALL {
    WITH main_node
    MATCH (main_node)-[:CONTAINS*0..]->(math:Math)
    RETURN COLLECT(DISTINCT {
        uid: math.uid,
        latex: math.latex,
        type: 'Math'
    }) AS math_content
}

// Get all diagrams
CALL {
    WITH main_node
    MATCH (main_node)-[:CONTAINS*0..]->(diagram:Diagram)
    RETURN COLLECT(DISTINCT {
        uid: diagram.uid,
        path: diagram.path,
        description: diagram.description,
        type: 'Diagram'
    }) AS diagram_content
}

// Get all tables
CALL {
    WITH main_node
    MATCH (main_node)-[:CONTAINS*0..]->(table:Table)
    RETURN COLLECT(DISTINCT {
        uid: table.uid,
        title: table.title,
        table_id: table.table_id,
        headers: table.headers,
        rows: table.rows,
        type: 'Table'
    }) AS table_content
}

// Get referenced mathematical content from other sections
CALL {
    WITH main_node
    OPTIONAL MATCH (main_node)-[:REFERENCES]->(ref_math:Math)
    OPTIONAL MATCH (main_node)-[:REFERENCES]->(ref_table:Table)
    RETURN 
        COLLECT(DISTINCT {
            uid: ref_math.uid,
            latex: ref_math.latex,
            type: 'Referenced_Math'
        }) AS referenced_math,
        COLLECT(DISTINCT {
            uid: ref_table.uid,
            title: ref_table.title,
            table_id: ref_table.table_id,
            type: 'Referenced_Table'
        }) AS referenced_tables
}

RETURN 
    main_node,
    regular_content,
    math_content,
    diagram_content,
    table_content,
    referenced_math,
    referenced_tables
""" 

GET_SECTION_WITH_CONTENT = """
MATCH (s:Section {number: $section_number})
OPTIONAL MATCH (s)-[:CONTAINS*]->(child)
RETURN s as parent, COLLECT(child) as children
""" 