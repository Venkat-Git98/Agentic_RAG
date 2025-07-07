"""
Pydantic Models for Knowledge Graph API

This module defines the data structures for the knowledge graph API,
ensuring that the data sent to the frontend is well-formed and consistent.
"""

from typing import List, Dict, Any
from pydantic import BaseModel, Field

class NodeData(BaseModel):
    """
    Defines the 'data' payload for a graph node.
    """
    label: str = Field(..., description="The display name of the node.")
    properties: Dict[str, Any] = Field(default_factory=dict, description="A flexible object for additional node properties.")

class Node(BaseModel):
    """
    Represents a single node in the knowledge graph.
    """
    id: str = Field(..., description="Unique identifier for the node.")
    type: str = Field(..., description="Category of the node (e.g., 'documentNode', 'entityNode').")
    position: Dict[str, float] = Field(..., description="Initial position for rendering.")
    data: NodeData = Field(..., description="The payload containing the node's data.")

class Edge(BaseModel):
    """
    Represents a single edge (relationship) in the knowledge graph.
    """
    id: str = Field(..., description="A unique identifier for the edge.")
    source: str = Field(..., description="The ID of the source node.")
    target: str = Field(..., description="The ID of the target node.")
    label: str | None = Field(default=None, description="Optional: A label to display on the edge.")

class GraphResponse(BaseModel):
    """
    The overall response structure for a knowledge graph query.
    """
    nodes: List[Node] = Field(..., description="A list of all nodes in the graph.")
    edges: List[Edge] = Field(..., description="A list of all edges connecting the nodes.") 