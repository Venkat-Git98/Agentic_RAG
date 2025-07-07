"""
Knowledge Graph Service

This module provides the business logic for fetching and structuring
knowledge graph data.
"""

from typing import Dict, Any
from tools.neo4j_connector import Neo4jConnector
from knowledge_graph_models import GraphResponse

def get_knowledge_graph_service(query: str) -> Dict[str, Any]:
    """
    Fetches and structures the knowledge graph data.

    Args:
        query: The user's query string.

    Returns:
        A dictionary containing the structured knowledge graph data.
    """
    raw_data = Neo4jConnector.get_knowledge_graph(query)
    
    # Validate the data with Pydantic models
    graph_response = GraphResponse(**raw_data)
    
    return graph_response.model_dump() 