"""
Rebuilds the Neo4j knowledge graph from the chunked pipeline output, embeds it,
and verifies the result. Use this to restore a lost or emptied database without
re-running the full (Gemini-heavy) ingestion pipeline.

Input (from pipeline step 5, not committed to git):
    output/5_chunked_knowledge_graph/nodes_chunked.jsonl
    output/5_chunked_knowledge_graph/edges_chunked.csv

Usage (from the Backend/ directory, with NEO4J_* and GOOGLE_API_KEY set):
    python data_ingestion_pipeline/load_and_embed.py            # load + index + embed + verify
    python data_ingestion_pipeline/load_and_embed.py --clear    # wipe the database first
    python data_ingestion_pipeline/load_and_embed.py --verify   # verify only, no writes

Every step is idempotent (MERGE + IF NOT EXISTS + embed-only-missing), so an
interrupted run can simply be re-run. Exits non-zero if verification fails.
"""
import sys
import os
import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
import logging
import json
import re

import google.generativeai as genai
from neo4j import GraphDatabase

# Ensure this directory is first on the path so `config` resolves to the pipeline config
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import config

sys.path.append(str(Path(__file__).parent / "unified_code"))
from pipeline_5_populate_embeddings import (
    create_vector_indexes, populate_embeddings, prepare_text_for_embedding,
    LABELS_TO_EMBED, EMBEDDING_MODEL, EMBEDDING_DIMENSIONS,
)

# --- Configuration ---
BASE_DIR = Path(__file__).parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)
CHUNKED_GRAPH_DIR = BASE_DIR / "output" / "5_chunked_knowledge_graph"
NODES_FILE = CHUNKED_GRAPH_DIR / "nodes_chunked.jsonl"
EDGES_FILE = CHUNKED_GRAPH_DIR / "edges_chunked.csv"
DATABASE = config.NEO4J_DATABASE
NODE_BATCH_SIZE = 500
EDGE_BATCH_SIZE = 1000

# Full-text indexes used by tools/keyword_retrieval_tool.py (kept in sync with manage_neo4j_indexes.py)
FULLTEXT_INDEXES = {
    "passage_content_idx": (["Passage"], ["text"]),
    "knowledge_base_text_idx": (["Chapter", "Section", "Subsection"], ["title", "text"]),
}

# --- Setup Logging ---
log_file_path = LOGS_DIR / "load_and_embed.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ],
    force=True,
)
logger = logging.getLogger(__name__)


def read_graph_files():
    """Reads the chunked graph files and returns (nodes, edges, uid->label map)."""
    nodes = []
    with open(NODES_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            node = json.loads(line)
            if node.get('label'):
                nodes.append(node)
    uid_to_label = {n['uid']: n['label'] for n in nodes}
    with open(EDGES_FILE, 'r', encoding='utf-8') as f:
        edges = list(csv.DictReader(f))
    return nodes, edges, uid_to_label


def delete_all_data(driver):
    """Deletes all nodes and relationships, in batches so large graphs don't exhaust transaction memory."""
    logger.info("--- Deleting all existing data from the database ---")
    with driver.session(database=DATABASE) as session:
        session.run("MATCH (n) CALL (n) { DETACH DELETE n } IN TRANSACTIONS OF 1000 ROWS")
    logger.info("Database cleared successfully.")


def create_constraints(driver, node_labels):
    """Creates uniqueness constraints on node UIDs for each label (these also index uid lookups)."""
    logger.info("--- Creating database constraints ---")
    with driver.session(database=DATABASE) as session:
        for label in node_labels:
            session.run(f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{label}) REQUIRE n.uid IS UNIQUE")
            logger.info(f"Constraint ensured for label: {label}")


def load_nodes(driver, nodes):
    """Loads nodes in batches per label. Nested dict/list properties are stored as JSON strings."""
    logger.info(f"--- Loading {len(nodes)} nodes ---")
    nodes_by_label = defaultdict(list)
    for node in nodes:
        properties = dict(node.get('properties', {}))
        # Neo4j cannot store nested maps, so serialize complex properties to JSON strings
        for key, value in properties.items():
            if isinstance(value, (dict, list)):
                properties[key] = json.dumps(value, ensure_ascii=False)
        properties['uid'] = node['uid']
        nodes_by_label[node['label']].append(properties)

    with driver.session(database=DATABASE) as session:
        for label, rows in nodes_by_label.items():
            for i in range(0, len(rows), NODE_BATCH_SIZE):
                session.run(f"""
                UNWIND $rows AS props
                MERGE (n:{label} {{uid: props.uid}})
                SET n += props
                """, rows=rows[i:i + NODE_BATCH_SIZE])
            logger.info(f"Loaded {len(rows)} nodes with label '{label}'")


def load_edges(driver, edges, uid_to_label):
    """
    Loads relationships grouped by (start label, type, end label), so every MATCH is
    label-qualified and backed by the uid constraint index (no APOC needed).
    Returns the number of edges skipped because an endpoint is missing from the nodes file.
    """
    logger.info(f"--- Loading {len(edges)} relationships ---")
    groups = defaultdict(list)
    skipped = []
    for edge in edges:
        start, end = edge['start_node_uid'], edge['end_node_uid']
        if start not in uid_to_label or end not in uid_to_label:
            skipped.append(edge)
            continue
        props = json.loads(edge.get('properties') or '{}')
        groups[(uid_to_label[start], edge['relationship_type'], uid_to_label[end])].append(
            {"start": start, "end": end, "props": props}
        )
    if skipped:
        logger.warning(f"Skipping {len(skipped)} relationships whose endpoints are not in the nodes file, e.g. "
                       f"{[(e['start_node_uid'], e['relationship_type'], e['end_node_uid']) for e in skipped[:3]]}")

    with driver.session(database=DATABASE) as session:
        for (start_label, rel_type, end_label), rows in groups.items():
            for i in range(0, len(rows), EDGE_BATCH_SIZE):
                session.run(f"""
                UNWIND $rows AS row
                MATCH (a:{start_label} {{uid: row.start}})
                MATCH (b:{end_label} {{uid: row.end}})
                MERGE (a)-[r:{rel_type}]->(b)
                SET r += row.props
                """, rows=rows[i:i + EDGE_BATCH_SIZE])
            logger.info(f"Loaded {len(rows)} ({start_label})-[:{rel_type}]->({end_label}) relationships")
    return len(skipped)


def create_fulltext_indexes(driver):
    logger.info("--- Creating full-text indexes ---")
    with driver.session(database=DATABASE) as session:
        for name, (labels, props) in FULLTEXT_INDEXES.items():
            session.run(f"CREATE FULLTEXT INDEX {name} IF NOT EXISTS "
                        f"FOR (n:{'|'.join(labels)}) ON EACH [{', '.join('n.' + p for p in props)}]")
            logger.info(f"Full-text index ensured: {name}")


def wait_for_indexes(driver, timeout_seconds=600):
    logger.info("--- Waiting for all indexes to come online ---")
    with driver.session(database=DATABASE) as session:
        session.run("CALL db.awaitIndexes($timeout)", timeout=timeout_seconds)
    logger.info("All indexes are online.")


def verify(driver, nodes, edges, uid_to_label):
    """Checks the database against the source files. Returns a list of failure messages."""
    logger.info("===== VERIFYING GRAPH =====")
    failures = []

    def check(ok, message):
        logger.info(f"[{'PASS' if ok else 'FAIL'}] {message}")
        if not ok:
            failures.append(message)

    expected_labels = Counter(n['label'] for n in nodes)
    expected_rels = Counter(e['relationship_type'] for e in edges
                            if e['start_node_uid'] in uid_to_label and e['end_node_uid'] in uid_to_label)
    expected_embeddings = Counter(
        n['label'] for n in nodes
        if n['label'] in LABELS_TO_EMBED and prepare_text_for_embedding(n).strip()
    )

    with driver.session(database=DATABASE) as session:
        # 1. Node counts per label
        for label, expected in sorted(expected_labels.items()):
            actual = session.run(f"MATCH (n:{label}) RETURN count(n) AS c").single()['c']
            check(actual == expected, f"{label} nodes: {actual} / {expected}")

        # 2. Relationship counts per type
        for rel_type, expected in sorted(expected_rels.items()):
            actual = session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) AS c").single()['c']
            check(actual == expected, f"{rel_type} relationships: {actual} / {expected}")

        # 3. Embeddings present with the right dimensions
        for label, expected in sorted(expected_embeddings.items()):
            row = session.run(f"""
                MATCH (n:{label}) WHERE n.embedding IS NOT NULL
                RETURN count(n) AS c, min(size(n.embedding)) AS min_dim, max(size(n.embedding)) AS max_dim
            """).single()
            check(row['c'] == expected, f"{label} embeddings: {row['c']} / {expected}")
            if row['c']:
                check(row['min_dim'] == row['max_dim'] == EMBEDDING_DIMENSIONS,
                      f"{label} embedding dimensions: {row['min_dim']}..{row['max_dim']} (expected {EMBEDDING_DIMENSIONS})")

        # 4. Indexes the backend depends on exist and are online
        indexes = {r['name']: r for r in session.run(
            "SHOW INDEXES YIELD name, type, state, populationPercent RETURN name, type, state, populationPercent")}
        required = [f"{label.lower()}_embedding_index" for label in LABELS_TO_EMBED] + list(FULLTEXT_INDEXES)
        for name in required:
            idx = indexes.get(name)
            check(idx is not None and idx['state'] == 'ONLINE' and idx['populationPercent'] == 100.0,
                  f"index {name}: {'missing' if idx is None else idx['state'] + ' ' + str(idx['populationPercent']) + '%'}")

        # 5. End-to-end semantic search sanity check (same model/dims the backend uses at query time)
        probe = "Where is an automatic sprinkler system required in Group A-2 occupancies?"
        query_vector = genai.embed_content(model=EMBEDDING_MODEL, content=probe, task_type="RETRIEVAL_DOCUMENT",
                                           output_dimensionality=EMBEDDING_DIMENSIONS)['embedding']
        hits = session.run("""
            CALL db.index.vector.queryNodes('passage_embedding_index', 5, $v) YIELD node, score
            RETURN node.uid AS uid, score, left(node.text, 120) AS snippet
        """, v=query_vector).data()
        for hit in hits:
            logger.info(f"    vector hit {hit['score']:.3f} {hit['uid']}: {hit['snippet']}")
        check(any(re.match(r'^903(\.|-)', h['uid']) for h in hits),
              "vector search for Group A-2 sprinkler requirements returns Section 903 (Automatic Sprinkler Systems) passages")

        # 6. Full-text search sanity check
        ft = session.run("CALL db.index.fulltext.queryNodes('passage_content_idx', 'sprinkler') YIELD node RETURN count(node) AS c").single()['c']
        check(ft > 0, f"full-text search on Passage text returns results ({ft} hits for 'sprinkler')")

    if failures:
        logger.error(f"===== VERIFICATION FAILED: {len(failures)} check(s) failed =====")
    else:
        logger.info("===== VERIFICATION PASSED: graph, embeddings and indexes match the source files =====")
    return failures


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--clear", action="store_true", help="delete all data in the database before loading")
    parser.add_argument("--verify", action="store_true", help="only verify the database against the source files")
    args = parser.parse_args()

    if not (NODES_FILE.exists() and EDGES_FILE.exists()):
        logger.error(f"Chunked graph files not found in '{CHUNKED_GRAPH_DIR}'. Halting.")
        sys.exit(1)
    if not all([config.NEO4J_URI, config.NEO4J_USERNAME, config.NEO4J_PASSWORD, config.GOOGLE_API_KEY]):
        logger.error("NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD and GOOGLE_API_KEY must be set. Halting.")
        sys.exit(1)

    genai.configure(api_key=config.GOOGLE_API_KEY)
    nodes, edges, uid_to_label = read_graph_files()
    logger.info(f"Source files: {len(nodes)} nodes, {len(edges)} relationships. "
                f"Embedding model: {EMBEDDING_MODEL} ({EMBEDDING_DIMENSIONS} dims)")

    driver = GraphDatabase.driver(config.NEO4J_URI, auth=(config.NEO4J_USERNAME, config.NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        with driver.session(database=DATABASE) as session:
            db_name = session.run("CALL db.info() YIELD name RETURN name").single()['name']
        logger.info(f"Connected to Neo4j at {config.NEO4J_URI} (database '{db_name}')")

        if not args.verify:
            logger.info("===== STARTING CHUNKED GRAPH LOAD AND EMBEDDING PIPELINE =====")
            if args.clear:
                delete_all_data(driver)
            create_constraints(driver, sorted(set(uid_to_label.values())))
            load_nodes(driver, nodes)
            load_edges(driver, edges, uid_to_label)
            create_fulltext_indexes(driver)
            create_vector_indexes(driver)
            wait_for_indexes(driver)
            failed_uids = populate_embeddings(driver)
            if failed_uids:
                logger.error(f"{len(failed_uids)} nodes were not embedded; re-run this script to retry them.")
            wait_for_indexes(driver)

        failures = verify(driver, nodes, edges, uid_to_label)
    finally:
        driver.close()
        logger.info("Neo4j connection closed.")

    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
