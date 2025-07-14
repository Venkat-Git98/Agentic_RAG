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
    GET_ENHANCED_SUBSECTION_CONTEXT,
    GET_CHAPTER_EQUATIONS,
    GET_SECTION_EQUATIONS,
    GET_EXPANDED_MATHEMATICAL_CONTEXT
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
        
        Enhanced to handle both Subsection and Section parent structures.
        """
        # Enhanced query that handles both Subsection and Section parent structures
        gold_standard_query = """
        MATCH (start_node {uid: $uid})
        
        // Try to find Subsection parent first (preferred structure)
        OPTIONAL MATCH (s:Subsection)
            WHERE (start_node:Subsection AND s=start_node) OR (s)-[:HAS_CHUNK|CONTAINS*]->(start_node)
        WITH start_node, s ORDER BY size(s.uid) ASC LIMIT 1
        
        // If no Subsection parent found, try Section parent (legacy structure)
        OPTIONAL MATCH (sec:Section)
        WHERE s IS NULL AND ((start_node:Section AND sec=start_node) OR (sec)-[:HAS_CHUNK|CONTAINS*]->(start_node))
        WITH start_node, COALESCE(s, sec) as final_parent
        WHERE final_parent IS NOT NULL

        // From the parent, get all DESCENDANTS (other subsections, passages, tables, math, etc.)
        OPTIONAL MATCH (final_parent)-[:HAS_CHUNK|CONTAINS*0..]->(descendant)

        // From those descendants, find any nodes they explicitly REFERENCE.
        WITH final_parent, COLLECT(DISTINCT descendant) AS descendants
        UNWIND descendants AS d
        OPTIONAL MATCH (d)-[:REFERENCES]->(referenced_node)
        WHERE referenced_node:Table OR referenced_node:Diagram OR referenced_node:Math

        // Collect all unique nodes we've found
        WITH final_parent, descendants, COLLECT(DISTINCT referenced_node) AS referenced_nodes
        // Combine the descendants and referenced nodes into a single list
        WITH final_parent, descendants + referenced_nodes AS all_nodes
        UNWIND all_nodes as node
        RETURN final_parent as parent, COLLECT(DISTINCT node) AS child_nodes
        """
        # Execute the query
        with Neo4jConnector.get_driver().session(database="neo4j") as session:
            result = session.run(gold_standard_query, uid=uid)
            record = result.single()

        if not record or not record["parent"]:
            # Fallback: if still no parent found, return just the original node
            logging.warning(f"No parent found for {uid}, using fallback to original node")
            return Neo4jConnector._get_fallback_context(uid)

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
    def _get_fallback_context(uid: str) -> Dict[str, Any]:
        """
        Fallback method when no parent structure is found.
        Returns just the original node as both primary and supplemental content.
        """
        query = """
        MATCH (n {uid: $uid})
        RETURN n
        """
        
        try:
            with Neo4jConnector.get_driver().session(database="neo4j") as session:
                result = session.run(query, uid=uid)
                record = result.single()
                
                if record and record['n']:
                    node = record['n']
                    
                    # Format the node
                    props = {
                        'uid': node.get('uid'),
                        'text': node.get('text'),
                        'title': node.get('title', ''),
                        'number': node.get('number', ''),
                        'type': list(node.labels)[0] if node.labels else 'Unknown'
                    }
                    
                    # If it's a passage, include it in supplemental context
                    if 'Passage' in node.labels:
                        return {
                            "primary_item": props,
                            "supplemental_context": {
                                "passages": [props],
                                "tables": [],
                                "mathematical_content": [],
                                "diagrams": []
                            }
                        }
                    else:
                        return {
                            "primary_item": props,
                            "supplemental_context": {
                                "passages": [],
                                "tables": [],
                                "mathematical_content": [],
                                "diagrams": []
                            }
                        }
        except Exception as e:
            logging.error(f"Error in fallback context for {uid}: {e}")
        
        # Ultimate fallback
        return {"primary_item": {}, "supplemental_context": {}}

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
        This method now uses a more robust query to gather all nodes and edges.
        """
        cypher_query = """
        MATCH (n)
        WHERE n.uid STARTS WITH $query
        WITH COLLECT(n) AS nodes
        UNWIND nodes AS n
        OPTIONAL MATCH (n)-[r]-(m)
        WHERE m IN nodes
        WITH nodes, COLLECT(DISTINCT r) AS relationships
        RETURN nodes, relationships
        """
        parameters = {"query": query}
        records = Neo4jConnector.execute_query(cypher_query, parameters)

        if not records:
            return {"nodes": [], "edges": []}

        record = records[0]
        db_nodes = record.get("nodes", [])
        db_relationships = record.get("relationships", [])

        nodes = []
        edges = []
        node_ids = set()

        for node_obj in db_nodes:
            uid = node_obj.get("uid")
            if uid and uid not in node_ids:
                node_ids.add(uid)
                nodes.append({
                    "id": uid,
                    "type": list(node_obj.labels)[0],
                    "position": {"x": 0, "y": 0},
                    "data": {
                        "label": node_obj.get("title", uid),
                        "properties": dict(node_obj)
                    }
                })

        if db_relationships:
            for rel in db_relationships:
                start_node_uid = rel.start_node.get("uid")
                end_node_uid = rel.end_node.get("uid")

                if start_node_uid and end_node_uid:
                    edges.append({
                        "id": rel.element_id,
                        "source": start_node_uid,
                        "target": end_node_uid,
                        "label": rel.type
                    })

        return {"nodes": nodes, "edges": edges}
    
    @staticmethod
    def get_enhanced_subsection_context(uid: str) -> Dict[str, Any]:
        """
        Enhanced subsection context retrieval that explicitly includes Math, Diagram, and Table nodes.
        This provides comprehensive context for mathematical content analysis.
        """
        try:
            with Neo4jConnector.get_driver().session(database="neo4j") as session:
                result = session.run(GET_ENHANCED_SUBSECTION_CONTEXT, uid=uid)
                record = result.single()

            if not record or not record["parent"]:
                return {}

            # Extract data from the record
            parent_node = record["parent"]
            content_nodes = record.get("content_nodes", [])
            math_nodes = record.get("math_nodes", [])
            diagram_nodes = record.get("diagram_nodes", [])
            table_nodes = record.get("table_nodes", [])
            referenced_math = record.get("referenced_math", [])
            referenced_tables = record.get("referenced_tables", [])

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
                    props['headers'] = n.get('headers', [])
                    props['rows'] = n.get('rows', [])
                    props['title'] = n.get('title', '')
                    props['table_id'] = n.get('table_id', '')
                elif 'Math' in n.labels:
                    props['latex'] = n.get('latex')
                elif 'Diagram' in n.labels:
                    props['path'] = n.get('path')
                    props['description'] = n.get('description', '')
                    
                return props

            parent_data = format_node(parent_node)

            # Organize all content by type
            content_map = {
                "passages": [format_node(node) for node in content_nodes if node],
                "tables": [format_node(node) for node in table_nodes if node] + [format_node(node) for node in referenced_tables if node],
                "mathematical_content": [format_node(node) for node in math_nodes if node] + [format_node(node) for node in referenced_math if node],
                "diagrams": [format_node(node) for node in diagram_nodes if node]
            }

            # Filter out None values
            for key in content_map:
                content_map[key] = [item for item in content_map[key] if item is not None]

            return {
                "primary_item": parent_data,
                "supplemental_context": content_map
            }
            
        except Exception as e:
            logging.error(f"Error getting enhanced subsection context for {uid}: {e}")
            return {}

    @staticmethod
    def get_chapter_overview_by_id(chapter_id: str) -> Dict[str, Any]:
        """
        Get a chapter overview by chapter ID, listing all sections in the chapter.
        This is used for chapter-level direct retrieval.
        
        Args:
            chapter_id: The chapter number (e.g., "19", "16")
            
        Returns:
            Dictionary with chapter information and list of sections
        """
        try:
            with Neo4jConnector.get_driver().session(database="neo4j") as session:
                result = session.run(GET_CHAPTER_OVERVIEW_BY_ID, uid=chapter_id)
                record = result.single()

            if not record:
                logging.warning(f"No chapter found with ID: {chapter_id}")
                return {}

            # Extract data from the record
            chapter_title = record.get("chapter_title", f"Chapter {chapter_id}")
            chapter_number = record.get("chapter_number", chapter_id)
            sections = record.get("sections", [])

            # Format the chapter overview
            formatted_sections = []
            for section in sections:
                formatted_sections.append({
                    'uid': section.get('uid'),
                    'title': section.get('title'),
                    'number': section.get('number'),
                    'type': 'Section'
                })

            # Format as a context block similar to other retrieval methods
            chapter_overview = {
                'uid': chapter_id,
                'title': chapter_title,
                'number': chapter_number,
                'type': 'Chapter',
                'text': f"Chapter {chapter_number}: {chapter_title}\n\nThis chapter contains {len(formatted_sections)} sections:\n" + 
                       '\n'.join([f"- Section {s['number']}: {s['title']}" for s in formatted_sections])
            }

            return {
                "primary_item": chapter_overview,
                "supplemental_context": {
                    "passages": [],
                    "tables": [],
                    "mathematical_content": [],
                    "diagrams": [],
                    "sections": formatted_sections
                }
            }
            
        except Exception as e:
            logging.error(f"Error getting chapter overview for {chapter_id}: {e}")
            return {}
    
    @staticmethod
    def get_chapter_equations(chapter_number: str) -> List[Dict[str, Any]]:
        """
        Retrieve all mathematical equations from a specific chapter.
        
        Args:
            chapter_number: Chapter number (e.g., "16")
            
        Returns:
            List of equation dictionaries
        """
        try:
            records = Neo4jConnector.execute_query(GET_CHAPTER_EQUATIONS, {"chapter_number": chapter_number})
            return [dict(record) for record in records]
        except Exception as e:
            logging.error(f"Failed to get equations for chapter {chapter_number}: {e}")
            return []
    
    @staticmethod
    def get_section_equations(section_number: str) -> List[Dict[str, Any]]:
        """
        Retrieve all mathematical equations from a specific section or subsection.
        
        Args:
            section_number: Section number (e.g., "1607.12.1")
            
        Returns:
            List of equation dictionaries
        """
        try:
            records = Neo4jConnector.execute_query(GET_SECTION_EQUATIONS, {"section_number": section_number})
            return [dict(record) for record in records]
        except Exception as e:
            logging.error(f"Failed to get equations for section {section_number}: {e}")
            return []
    
    @staticmethod
    def get_expanded_mathematical_context(uid: str) -> Dict[str, Any]:
        """
        Get comprehensive mathematical context for a section with explicit content separation.
        
        Args:
            uid: Section or subsection number (e.g., "1607.12")
            
        Returns:
            Dictionary with separated regular content, math content, diagrams, and tables
        """
        try:
            records = Neo4jConnector.execute_query(GET_EXPANDED_MATHEMATICAL_CONTEXT, {"uid": uid})
            if not records:
                return {}
            
            record = records[0]
            return {
                "main_node": dict(record.get("main_node", {})),
                "regular_content": record.get("regular_content", []),
                "math_content": record.get("math_content", []),
                "diagram_content": record.get("diagram_content", []),
                "table_content": record.get("table_content", []),
                "referenced_math": record.get("referenced_math", []),
                "referenced_tables": record.get("referenced_tables", [])
            }
        except Exception as e:
            logging.error(f"Failed to get expanded mathematical context for '{uid}': {e}")
            return {}

# Ensure the driver is closed when the application exits.
    @staticmethod
    def get_chapter_content(chapter_number: str) -> Dict[str, Any]:
        """
        Retrieves all content (sections, subsections, passages, tables, math, diagrams)
        for a given chapter.

        Args:
            chapter_number: The number of the chapter (e.g., "3").

        Returns:
            A dictionary containing the chapter's content, structured by type.
        """
        logging.info(f"Retrieving all content for Chapter {chapter_number}")
        
        query = """
        MATCH (c:Chapter {number: $chapter_number})
        OPTIONAL MATCH (c)-[:CONTAINS*]->(node)
        WHERE node:Section OR node:Subsection OR node:Passage OR node:Table OR node:Math OR node:Diagram
        RETURN 
            c.uid AS chapter_uid,
            c.title AS chapter_title,
            c.number AS chapter_number,
            COLLECT(DISTINCT CASE WHEN node:Section THEN {uid: node.uid, title: node.title, number: node.number, type: LABELS(node)[0]} ELSE NULL END) AS sections,
            COLLECT(DISTINCT CASE WHEN node:Subsection THEN {uid: node.uid, title: node.title, number: node.number, type: LABELS(node)[0]} ELSE NULL END) AS subsections,
            COLLECT(DISTINCT CASE WHEN node:Passage THEN {uid: node.uid, text: node.text, type: LABELS(node)[0]} ELSE NULL END) AS passages,
            COLLECT(DISTINCT CASE WHEN node:Table THEN {uid: node.uid, title: node.title, html_repr: node.html_repr, type: LABELS(node)[0]} ELSE NULL END) AS tables,
            COLLECT(DISTINCT CASE WHEN node:Math THEN {uid: node.uid, latex: node.latex, type: LABELS(node)[0]} ELSE NULL END) AS mathematical_content,
            COLLECT(DISTINCT CASE WHEN node:Diagram THEN {uid: node.uid, path: node.path, description: node.description, type: LABELS(node)[0]} ELSE NULL END) AS diagrams
        """
        
        try:
            with Neo4jConnector.get_driver().session(database="neo4j") as session:
                result = session.run(query, chapter_number=chapter_number)
                record = result.single()

            if not record:
                logging.warning(f"No content found for Chapter {chapter_number}")
                return {}

            # Filter out None values from collected lists
            sections = [s for s in record["sections"] if s is not None]
            subsections = [s for s in record["subsections"] if s is not None]
            passages = [p for p in record["passages"] if p is not None]
            tables = [t for t in record["tables"] if t is not None]
            mathematical_content = [m for m in record["mathematical_content"] if m is not None]
            diagrams = [d for d in record["diagrams"] if d is not None]

            return {
                "chapter_uid": record["chapter_uid"],
                "chapter_title": record["chapter_title"],
                "chapter_number": record["chapter_number"],
                "sections": sections,
                "subsections": subsections,
                "passages": passages,
                "tables": tables,
                "mathematical_content": mathematical_content,
                "diagrams": diagrams
            }

        except Exception as e:
            logging.error(f"Error retrieving chapter content for Chapter {chapter_number}: {e}")
            return {}

atexit.register(Neo4jConnector.close_driver)