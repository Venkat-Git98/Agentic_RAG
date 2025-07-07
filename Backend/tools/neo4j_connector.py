"""
This module provides a singleton connector to a Neo4j database,
handling the driver lifecycle and executing Cypher queries, particularly for vector search.
"""
from __future__ import annotations
import logging
import atexit
import json

from neo4j import GraphDatabase
from neo4j.graph import Node
from config import (
    NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD,
    EMBEDDING_MODEL, TIER_1_MODEL_NAME
)
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List

import google.generativeai as genai
from .direct_retrieval_queries import (
    GET_CHAPTER_OVERVIEW_BY_ID,
    GET_SUBSECTION_CONTEXT_BY_ID,
    GET_SECTION_CONTEXT_BY_ID,
    GET_FULL_SUBSECTION_HIERARCHY,
)

class Neo4jConnector:
    """
    A singleton class to manage the Neo4j database connection driver.
    """
    _driver = None

    @classmethod
    def get_driver(cls):
        """
        Gets the singleton Neo4j driver instance. Initializes it if necessary.
        """
        if cls._driver is None:
            logging.info("Initializing Neo4j driver...")
            try:
                cls._driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
                # Verify connection
                cls._driver.verify_connectivity()
                logging.info("Neo4j driver initialized successfully.")
            except Exception as e:
                logging.error(f"FATAL: Could not initialize Neo4j driver: {e}")
                raise
        return cls._driver

    @classmethod
    def close_driver(cls):
        """
        Closes the Neo4j driver connection if it exists.
        """
        if cls._driver is not None:
            logging.info("Closing Neo4j driver.")
            cls._driver.close()
            cls._driver = None

    @staticmethod
    def execute_query(query: str, parameters: dict = None) -> list:
        """
        Executes a read query against the database.

        Args:
            query: The Cypher query string to execute.
            parameters: A dictionary of parameters to pass to the query.

        Returns:
            A list of records from the query result.
        """
        driver = Neo4jConnector.get_driver()
        records, summary, keys = driver.execute_query(query, parameters or {}, database_="neo4j")
        return records

    @staticmethod
    def vector_search(embedding: list, top_k: int = 1) -> list[dict]:
        """
        Performs a hybrid vector search and graph context expansion.

        This method first performs a vector search to find the single best matching node.
        It then uses that node's UID to retrieve a "gold standard" context, which
        includes the node's parent subsection and all of its immediate child nodes
        (passages, tables, diagrams, math, etc.), providing a comprehensive
        and structured context for the query.

        Args:
            embedding: The embedding vector of the query document.
            top_k: The number of top similar documents to return (fixed to 1 to get the best match).

        Returns:
            A list containing a single dictionary that represents the comprehensive context
            for the best-matching node.
        """
        # Step 1: Find the single best matching node via vector search.
        query = """
        CALL db.index.vector.queryNodes('passage_embedding_index', 1, $embedding)
        YIELD node, score
        RETURN node.uid AS uid, score
        """
        parameters = {"embedding": embedding}
        driver = Neo4jConnector.get_driver()
        records, _, _ = driver.execute_query(query, parameters, database_="neo4j")

        if not records:
            return []

        # Step 2: Use the UID of the best match to get the full "gold standard" context.
        best_match_uid = records[0].data().get("uid")
        if not best_match_uid:
            return []
            
        logging.info(f"Vector search found best match: {best_match_uid}. Expanding context via graph.")
        # The result of get_gold_standard_context is a dictionary, so we wrap it in a list
        # to match the expected return type of the other retrieval functions.
        gold_standard_context = Neo4jConnector.get_gold_standard_context(best_match_uid)
        
        # Ensure the output is a list of dictionaries, even if only one item is returned.
        if gold_standard_context:
            return [gold_standard_context]
        else:
            return []

    @staticmethod
    def get_related_nodes_for_parent(parent_uid: str) -> list:
        """
        Finds all Table and Diagram nodes that are children of a given parent UID.
        This relies on the specific graph schema where a parent (e.g., a Subsection)
        is connected to its children (Passages, Tables, etc.) via a 'HAS_CHUNK' relationship.

        Args:
            parent_uid: The UID of the parent entity (e.g., '1609.1.1').

        Returns:
            A list of dictionaries, each representing a related Table or Diagram.
        """
        if not parent_uid:
            return []
        
        # This query finds the parent subsection using its UID, then finds all
        # connected Table or Diagram nodes via the 'HAS_CHUNK' relationship.
        query = """
        MATCH (parent {uid: $parent_uid})<-[r:HAS_CHUNK]-(child)
        WHERE child:Table OR child:Diagram
        RETURN
            child.uid AS uid,
            child.text AS text,
            labels(child)[0] AS type
        """
        parameters = {"parent_uid": parent_uid}
        driver = Neo4jConnector.get_driver()
        try:
            records, _, _ = driver.execute_query(query, parameters, database_="neo4j")
            return [record.data() for record in records]
        except Exception as e:
            logging.error(f"Failed to get related nodes for parent_uid '{parent_uid}': {e}")
            return []

    @staticmethod
    def inspect_node_neighborhood(uid: str) -> list:
        """
        A debugging utility to inspect the direct relationships of a node.
        Returns a list of relationship data.
        """
        query = """
        MATCH (n {uid: $uid})-[r]-(neighbor)
        RETURN
            n.uid as start_node_uid,
            labels(n) as start_node_labels,
            type(r) as relationship_type,
            neighbor.uid as neighbor_node_uid,
            labels(neighbor) as neighbor_node_labels
        LIMIT 25
        """
        parameters = {"uid": uid}
        driver = Neo4jConnector.get_driver()
        try:
            records, _, _ = driver.execute_query(query, parameters, database_="neo4j")
            return [record.data() for record in records]
        except Exception as e:
            logging.error(f"Failed to inspect neighborhood for node '{uid}': {e}")
            return []

    @staticmethod
    def get_parent_metadata(parent_uid: str) -> dict:
        """
        Fetches the metadata for a given parent node (e.g., a Subsection).
        
        Args:
            parent_uid: The UID of the parent entity.

        Returns:
            A dictionary containing the parent's metadata, or an empty dict if not found.
        """
        if not parent_uid:
            return {}
        
        query = """
        MATCH (p {uid: $parent_uid})
        RETURN
            p.uid AS uid,
            p.title AS title,
            p.number AS number
        LIMIT 1
        """
        parameters = {"parent_uid": parent_uid}
        driver = Neo4jConnector.get_driver()
        try:
            records, _, _ = driver.execute_query(query, parameters, database_="neo4j")
            return records[0].data() if records else {}
        except Exception as e:
            logging.error(f"Failed to get metadata for parent '{parent_uid}': {e}")
            return {}

    @staticmethod
    def inspect_node_and_neighborhood(uid: str) -> dict:
        """
        Fetches a node's properties, labels, and all its relationships (in and out).
        This is a powerful debugging tool to understand the graph structure.
        """
        query = """
        MATCH (n {uid: $uid})
        OPTIONAL MATCH (n)-[r]->(peer_out)
        OPTIONAL MATCH (n)<-[l]-(peer_in)
        RETURN
            n,
            collect(DISTINCT {rel_type: type(r), direction: 'out', peer_node: peer_out}) AS outgoing,
            collect(DISTINCT {rel_type: type(l), direction: 'in',  peer_node: peer_in}) AS incoming
        """
        parameters = {"uid": uid}
        driver = Neo4jConnector.get_driver()
        try:
            records, _, _ = driver.execute_query(query, parameters, database_="neo4j")
            if not records:
                return {"error": f"Node with uid '{uid}' not found."}

            record = records[0]
            node_data = record.get("n", {})
            
            def format_rel(rel):
                peer_node = rel.get('peer_node')
                if not peer_node: return None
                return {
                    "rel_type": rel.get('rel_type'),
                    "direction": rel.get('direction'),
                    "peer_labels": list(peer_node.labels),
                    "peer_properties": dict(peer_node)
                }

            outgoing_rels = [formatted for rel in record.get("outgoing", []) if (formatted := format_rel(rel))]
            incoming_rels = [formatted for rel in record.get("incoming", []) if (formatted := format_rel(rel))]
            
            return {
                "node_uid": uid,
                "node_labels": list(node_data.labels),
                "node_properties": dict(node_data),
                "relationships": outgoing_rels + incoming_rels
            }
        except Exception as e:
            logging.error(f"Failed to inspect node '{uid}': {e}")
            return {"error": str(e)}

    @staticmethod
    def get_gold_standard_context(uid: str) -> Dict[str, Any]:
        """
        Given a UID of a node from the vector search, this function expands the context
        to a "gold standard" chunk.

        If the node is a Passage or Math chunk, it retrieves the parent Subsection and
        all of its children (other Passages, Math, and Tables).

        If the node is a Table, it retrieves the table and its parent subsection.
        """
        # This new query first finds the ultimate parent of any given node
        # before gathering all of its descendants, ensuring full context.
        gold_standard_query = """
        MATCH (start_node {uid: $uid})
        // Find the top-level Subsection parent of the starting node.
        // This handles cases where we start in a child node (Passage, etc.)
        CALL (start_node) {
            MATCH (s:Subsection)
            WHERE (start_node:Subsection AND s=start_node) OR (s)-[:HAS_CHUNK|CONTAINS*]->(start_node)
            WITH s ORDER BY size(s.uid) ASC LIMIT 1
            RETURN s as parent
        }

        // From the true parent, get all DESCENDANTS (other subsections, passages, tables, math, etc.)
        OPTIONAL MATCH (parent)-[:HAS_CHUNK|CONTAINS*0..]->(descendant)

        // From those descendants, find any nodes they explicitly REFERENCE.
        WITH parent, COLLECT(DISTINCT descendant) AS descendants
        UNWIND descendants AS d
        OPTIONAL MATCH (d)-[:REFERENCES]->(referenced_node)
        WHERE referenced_node:Table OR referenced_node:Diagram OR referenced_node:Math

        // Collect all unique nodes we've found
        WITH parent, descendants, COLLECT(DISTINCT referenced_node) AS referenced_nodes
        // Combine the descendants and referenced nodes into a single list
        WITH parent, descendants + referenced_nodes AS all_nodes
        UNWIND all_nodes as node
        RETURN parent, COLLECT(DISTINCT node) AS child_nodes
        """
        # Execute the query
        with Neo4jConnector.get_driver().session(database="neo4j") as session:
            result = session.run(gold_standard_query, uid=uid)
            record = result.single()

        if not record or not record["parent"]:
            return {"primary_item": {}, "supplemental_context": {}}

        # Format the data into a structured dictionary
        parent_node = record["parent"]
        child_nodes = record.get("child_nodes", [])
        
        def format_node(n: Node) -> Dict[str, Any]:
            if not n:
                return None
            
            # Default properties
            props = {
                'uid': n.get('uid'),
                'text': n.get('text'),
                'title': n.get('title'),
                'number': n.get('number'),
                'type': list(n.labels)[0] if n.labels else 'Unknown'
            }
            # Add table data if it's a table
            if 'Table' in n.labels:
                props['html_repr'] = n.get('html_repr', n.get('text'))
                # Extract actual table data for processing
                import json
                try:
                    # Parse headers from JSON string if needed
                    headers = n.get('headers', [])
                    if isinstance(headers, str):
                        headers = json.loads(headers)
                    props['headers'] = headers
                    
                    # Parse rows from JSON string if needed
                    rows = n.get('rows', [])
                    if isinstance(rows, str):
                        rows = json.loads(rows)
                    props['rows'] = rows
                    
                    props['title'] = n.get('title', '')
                    props['table_id'] = n.get('table_id', '')
                except json.JSONDecodeError as e:
                    # If JSON parsing fails, use empty defaults
                    props['headers'] = []
                    props['rows'] = []
                    props['title'] = n.get('title', '')
                    props['table_id'] = n.get('table_id', '')
            # Add latex if it's math
            if 'Math' in n.labels:
                props['latex'] = n.get('latex')
            # Add path if it's a diagram
            if 'Diagram' in n.labels:
                props['path'] = n.get('path')

            return props

        parent_data = format_node(parent_node)
        
        # Organize children by type for cleaner output
        content_map = {
            "passages": [],
            "tables": [],
            "mathematical_content": [],
            "diagrams": []
        }

        # Convert each raw Neo4j Node into a plain dict first, then bucket it.
        for raw_child in child_nodes:
            formatted_child = format_node(raw_child)
            if not formatted_child:
                continue

            # Skip if somehow we picked up the parent again
            if formatted_child.get("uid") == parent_data.get("uid"):
                continue

            node_type = formatted_child.get("type", "Unknown").lower()

            if any(keyword in node_type for keyword in ["passage", "subsection", "section"]):
                content_map["passages"].append(formatted_child)
            elif "table" in node_type:
                content_map["tables"].append(formatted_child)
            elif "math" in node_type:
                content_map["mathematical_content"].append(formatted_child)
            elif "diagram" in node_type:
                content_map["diagrams"].append(formatted_child)

        return {"primary_item": parent_data, "supplemental_context": content_map}

    @staticmethod
    def get_node_by_uid(uid: str) -> Node | None:
        """Finds and returns a single node by its UID."""
        records = Neo4jConnector.execute_query("MATCH (n {uid: $uid}) RETURN n", {"uid": uid})
        return records[0]["n"] if records else None

    @staticmethod
    def get_all_children_of_node(uid: str) -> list[Node]:
        """
        Retrieves all direct children of a given node, following any outgoing relationship.
        """
        query = "MATCH (parent {uid: $uid})-[]->(child) RETURN child"
        records = Neo4jConnector.execute_query(query, {"uid": uid})
        return [record["child"] for record in records]

    @staticmethod
    def get_all_descendants_of_node(uid: str) -> list[Node]:
        """
        Retrieves all descendants of a given node, following any outgoing relationship
        recursively down the graph.
        """
        query = "MATCH (parent {uid: $uid})-[*]->(descendant) RETURN DISTINCT descendant"
        records = Neo4jConnector.execute_query(query, {"uid": uid})
        return [record["descendant"] for record in records]

    @staticmethod
    def get_full_subsection_context_by_id(uid: str) -> Dict[str, Any]:
        """
        Given a subsection UID (e.g., "1607.12"), retrieves that subsection
        and its entire hierarchy of descendants (children, grandchildren, etc.).

        This is a powerful fallback query to get maximum context.
        """
        query = """
        MATCH (parent:Subsection {uid: $uid})
        
        // Get all descendants recursively
        OPTIONAL MATCH (parent)-[:HAS_CHUNK|CONTAINS*0..]->(descendant)
        
        // Also get any referenced nodes (tables, equations, diagrams)
        WITH parent, COLLECT(DISTINCT descendant) AS descendants
        UNWIND descendants AS d
        OPTIONAL MATCH (d)-[:REFERENCES]->(referenced_node)
        WHERE referenced_node:Table OR referenced_node:Diagram OR referenced_node:Math
        
        // Collect everything
        WITH parent, descendants, COLLECT(DISTINCT referenced_node) AS referenced_nodes
        WITH parent, descendants + referenced_nodes AS all_nodes
        UNWIND all_nodes as node
        RETURN parent, COLLECT(DISTINCT node) AS child_nodes
        """
        
        try:
            with Neo4jConnector.get_driver().session(database="neo4j") as session:
                result = session.run(query, uid=uid)
                record = result.single()

            if not record or not record["parent"]:
                return {}

            # Format the data using the same helper function as get_gold_standard_context
            parent_node = record["parent"]
            child_nodes = record.get("child_nodes", [])
            
            def format_node(n: Node) -> Dict[str, Any]:
                if not n:
                    return None
                
                props = {
                    'uid': n.get('uid'),
                    'text': n.get('text'),
                    'title': n.get('title'),
                    'number': n.get('number'),
                    'type': list(n.labels)[0] if n.labels else 'Unknown'
                }
                if 'Table' in n.labels:
                    props['html_repr'] = n.get('html_repr', n.get('text'))
                    # Extract actual table data for processing
                    import json
                    try:
                        # Parse headers from JSON string if needed
                        headers = n.get('headers', [])
                        if isinstance(headers, str):
                            headers = json.loads(headers)
                        props['headers'] = headers
                        
                        # Parse rows from JSON string if needed
                        rows = n.get('rows', [])
                        if isinstance(rows, str):
                            rows = json.loads(rows)
                        props['rows'] = rows
                        
                        props['title'] = n.get('title', '')
                        props['table_id'] = n.get('table_id', '')
                    except json.JSONDecodeError as e:
                        # If JSON parsing fails, use empty defaults
                        props['headers'] = []
                        props['rows'] = []
                        props['title'] = n.get('title', '')
                        props['table_id'] = n.get('table_id', '')
                if 'Math' in n.labels:
                    props['latex'] = n.get('latex')
                if 'Diagram' in n.labels:
                    props['path'] = n.get('path')
                return props

            parent_data = format_node(parent_node)
            
            # Organize children by type
            content_map = {
                "passages": [],
                "tables": [],
                "mathematical_content": [],
                "diagrams": []
            }

            # This makes the function robust to different input structures.
            for child in child_nodes:
                if not isinstance(child, dict): continue
                node_type = child.get('type', 'Unknown').lower()
                if 'passage' in node_type or 'subsection' in node_type or 'section' in node_type:
                    content_map["passages"].append(child)
                elif 'table' in node_type:
                    content_map["tables"].append(child)
                elif 'math' in node_type:
                    content_map["mathematical_content"].append(child)
                elif 'diagram' in node_type:
                    content_map["diagrams"].append(child)

            # Return a list containing a single, well-structured context block
            return [{
                "primary_item": parent_data,
                "supplemental_context": content_map
            }]
            
        except Exception as e:
            logging.error(f"Error getting full subsection context for {uid}: {e}")
            return {}

    @staticmethod
    def direct_lookup(entity_type: str, entity_id: str) -> Dict[str, Any]:
        """
        Performs a direct lookup for a specific entity (e.g., Subsection, Table)
        using a predefined Cypher query.

        Args:
            entity_type: The type of entity to look up (e.g., "Subsection").
            entity_id: The UID of the entity to look up.

        Returns:
            A dictionary containing the formatted data of the entity.
        """
        logging.info(f"Performing direct lookup for {entity_type} with ID '{entity_id}'")
        query_map = {
            "Subsection": GET_SUBSECTION_CONTEXT_BY_ID,
            "Chapter": GET_CHAPTER_OVERVIEW_BY_ID,
            "Section": GET_SECTION_CONTEXT_BY_ID,
        }

        query = query_map.get(entity_type)
        if not query:
            logging.warning(f"No predefined query for entity type: {entity_type}")
            return {"error": f"Unknown entity type for direct lookup: {entity_type}"}

        try:
            with Neo4jConnector.get_driver().session(database="neo4j") as session:
                result = session.run(query, uid=entity_id)
                record = result.single()

            if not record:
                return {"error": f"{entity_type} with ID '{entity_id}' not found."}

            logging.info(f"Direct lookup successful for {entity_type} ID '{entity_id}'.")
            return record.data()

        except Exception as e:
            logging.error(f"Error during direct lookup for {entity_type} ID '{entity_id}': {e}")
            return {"error": str(e)}

    @staticmethod
    def list_vector_indexes() -> list:
        """
        Lists all available vector indexes in the database.
        Useful for debugging index name mismatches.

        Returns:
            A list of index metadata dictionaries.
        """
        driver = Neo4jConnector.get_driver()
        try:
            # The result_transformer is used to convert the records directly into a list of dicts
            indexes, _, _ = driver.execute_query(
                "SHOW VECTOR INDEXES",
                database_="neo4j"
            )
            return [idx.data() for idx in indexes]
        except Exception as e:
            logging.error(f"Failed to list vector indexes: {e}")
            return []

    @staticmethod
    def create_vector_index_if_not_exists():
        """
        Checks if the 'passage_embeddings' vector index exists and creates it if not.
        """
        driver = Neo4jConnector.get_driver()
        
        # Check if the index exists
        try:
            # This query will list all vector indexes. We can check if ours is in the list.
            indexes = driver.execute_query(
                "SHOW VECTOR INDEXES", database_="neo4j", result_transformer_=lambda r: r.data()
            )
            index_exists = any(idx['name'] == 'passage_embeddings' for idx in indexes)

            if index_exists:
                logging.info("Vector index 'passage_embeddings' already exists.")
                return

            # If not, create it
            logging.info("Vector index 'passage_embeddings' not found. Creating it now...")
            # This creates a vector index on the 'Passage' nodes using the 'embedding' property.
            # It uses cosine similarity and a 1536-dimensional vector.
            # NOTE: The dimension (1536) should match your embedding model's output.
            # For Gemini models, 768 is a common dimension. Let's assume that for now.
            # For 'models/embedding-001', the dimension is 768.
            index_query = """
            CREATE VECTOR INDEX passage_embeddings IF NOT EXISTS
            FOR (p:Passage) ON (p.embedding)
            OPTIONS {indexConfig: {
                `vector.dimensions`: 768,
                `vector.similarity_function`: 'cosine'
            }}
            """
            driver.execute_query(index_query, database_="neo4j")
            logging.info("Vector index 'passage_embeddings' created successfully.")

        except Exception as e:
            logging.error(f"Error during vector index check/creation: {e}")
            # It's safer to re-raise the exception to halt execution if we can't ensure
            # the index is ready, as subsequent queries will fail.
            raise

    @staticmethod
    def comprehensive_vector_search(embedding: list, top_k: int = 3) -> list:
        """
        Searches across Passage, Table, and Diagram indexes simultaneously.
        """
        # A list of indexes to search. You confirmed these exist.
        indexes = ["passage_embedding_index", "table_embedding_index", "diagram_embedding_index"]
        all_results = []
        
        with ThreadPoolExecutor() as executor:
            future_to_index = {
                executor.submit(Neo4jConnector.vector_search_single_index, index, embedding, top_k): index
                for index in indexes
            }
            for future in as_completed(future_to_index):
                try:
                    all_results.extend(future.result())
                except Exception as e:
                    logging.error(f"Error querying index {future_to_index[future]}: {e}")

        # De-duplicate results based on node UID and take the highest score
        unique_results = {}
        for res in all_results:
            uid = res['uid']
            if uid not in unique_results or res['score'] > unique_results[uid]['score']:
                unique_results[uid] = res
        
        # Sort by score and return the top_k
        sorted_results = sorted(unique_results.values(), key=lambda x: x['score'], reverse=True)
        return sorted_results[:top_k]
    
    @staticmethod
    def vector_search_single_index(index_name: str, embedding: list, top_k: int) -> list:
        """Helper to search a single vector index."""
        # The index name must be directly embedded in the query string for the
        # procedure call. It cannot be passed as a parameter.
        query = f"""
        CALL db.index.vector.queryNodes('{index_name}', $top_k, $embedding)
        YIELD node, score
        RETURN
            node.uid AS uid,
            node.text AS text,
            node.parent_uid AS parent_uid,
            labels(node)[0] AS type,
            score
        """
        params = {"top_k": top_k, "embedding": embedding}
        driver = Neo4jConnector.get_driver()
        records, _, _ = driver.execute_query(query, params, database_="neo4j")
        return [r.data() for r in records]

    def keyword_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Performs a keyword-based search against the 'text' property of all nodes.
        This is a fallback for specific terms not well-suited for vector search.
        """
        # This query now uses a standard CONTAINS search, which is less performant
        # than a full-text index but does not require one to be created.
        cypher_query = """
        MATCH (n)\n        WHERE n.text CONTAINS $query\n        RETURN n.uid AS uid, n.text AS text, labels(n)[0] AS type, 0.9 AS score\n        LIMIT $top_k\n        """
        params = {"query": query, "top_k": top_k}
        records = self.execute_query(cypher_query, params)
        
        # Format the results into the standard context block structure
        context_blocks = []
        for record in records:
            context_blocks.append({
                "primary_item": {
                    "uid": record.get("uid"),
                    "text": record.get("text"),
                    "type": record.get("type")
                },
                "supplemental_context": {}
            })
        return context_blocks

    @staticmethod
    def get_knowledge_graph(query: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetches a knowledge graph based on a user's query string.

        Args:
            query: The user's query string.

        Returns:
            A dictionary containing the nodes and edges of the knowledge graph.
        """
        cypher_query = """
        MATCH (n)
        WHERE n.uid STARTS WITH $query
        OPTIONAL MATCH (n)-[r]-(m)
        RETURN n, r, m
        """
        parameters = {"query": query}
        records = Neo4jConnector.execute_query(cypher_query, parameters)

        nodes = []
        edges = []
        node_ids = set()

        for record in records:
            if record["n"] and record["n"]["uid"] not in node_ids:
                node_ids.add(record["n"]["uid"])
                nodes.append({
                    "id": record["n"]["uid"],
                    "type": list(record["n"].labels)[0],
                    "position": {"x": 0, "y": 0},
                    "data": {
                        "label": record["n"]["title"] if "title" in record["n"] else record["n"]["uid"],
                        "properties": dict(record["n"])
                    }
                })

            if record["m"] and record["m"]["uid"] not in node_ids:
                node_ids.add(record["m"]["uid"])
                nodes.append({
                    "id": record["m"]["uid"],
                    "type": list(record["m"].labels)[0],
                    "position": {"x": 0, "y": 0},
                    "data": {
                        "label": record["m"]["title"] if "title" in record["m"] else record["m"]["uid"],
                        "properties": dict(record["m"])
                    }
                })

            if record["r"]:
                edges.append({
                    "id": f'{record["r"].start_node["uid"]}-{record["r"].end_node["uid"]}',
                    "source": record["r"].start_node["uid"],
                    "target": record["r"].end_node["uid"],
                    "label": type(record["r"]).__name__
                })

        return {"nodes": nodes, "edges": edges}

# Ensure the driver is closed when the application exits.
atexit.register(Neo4jConnector.close_driver) 