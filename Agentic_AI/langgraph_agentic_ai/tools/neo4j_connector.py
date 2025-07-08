from typing import Dict, List, Any
from neo4j import GraphDatabase, Driver
import atexit

class Neo4jConnector:
    _driver: Driver = None

    @staticmethod
    def get_driver() -> Driver:
        if Neo4jConnector._driver is None:
            Neo4jConnector._driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
        return Neo4jConnector._driver

    @staticmethod
    def close_driver() -> None:
        if Neo4jConnector._driver is not None:
            Neo4jConnector._driver.close()

    @staticmethod
    def execute_query(query: str, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        with Neo4jConnector.get_driver().session() as session:
            records = session.run(query, parameters)
            return [r.data() for r in records]

    @staticmethod
    def get_knowledge_graph(query: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetches a knowledge graph based on a user's query string.
        This method now uses a more robust two-query approach to gather all nodes and edges.
        """
        # Step 1: Get all nodes matching the query prefix
        node_query = """
        MATCH (n)
        WHERE n.uid STARTS WITH $query
        RETURN n
        """
        parameters = {"query": query}
        node_records = Neo4jConnector.execute_query(node_query, parameters)

        nodes = []
        node_ids = set()

        for record in node_records:
            node = record["n"]
            if node and node["uid"] not in node_ids:
                node_id = node["uid"]
                node_ids.add(node_id)
                nodes.append({
                    "id": node_id,
                    "type": list(node.labels)[0],
                    "position": {"x": 0, "y": 0},
                    "data": {
                        "label": node.get("title", node.get("label", node_id)),
                        "properties": dict(node)
                    }
                })

        if not nodes:
            return {"nodes": [], "edges": []}

        # Step 2: Get all relationships between the collected nodes
        edge_query = """
        MATCH (n)-[r]-(m)
        WHERE n.uid IN $node_ids AND m.uid IN $node_ids
        RETURN r
        """
        edge_parameters = {"node_ids": list(node_ids)}
        edge_records = Neo4jConnector.execute_query(edge_query, edge_parameters)

        edges = []
        edge_ids = set()
        for record in edge_records:
            rel = record["r"]
            if rel and rel.element_id not in edge_ids:
                edge_ids.add(rel.element_id)
                start_node_uid = rel.start_node.get("uid")
                end_node_uid = rel.end_node.get("uid")

                # Ensure that both the start and end nodes of the edge are in the selected nodes
                if start_node_uid in node_ids and end_node_uid in node_ids:
                    edges.append({
                        "id": str(rel.element_id),
                        "from": str(start_node_uid),
                        "to": str(end_node_uid),
                        "label": rel.type
                    })

        return {"nodes": nodes, "edges": edges}

# Ensure the driver is closed when the application exits.
atexit.register(Neo4jConnector.close_driver)
