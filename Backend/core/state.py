"""
Enhanced state management for LangGraph-based agentic workflow.

This module defines the comprehensive state structure that flows through
all agents in the LangGraph workflow, maintaining compatibility with
the existing sophisticated memory management and tool systems.
"""

from __future__ import annotations
from typing import List, Dict, Any, Literal, Optional, Union
from typing_extensions import TypedDict
from pydantic import Field
from datetime import datetime
import json

class ExecutionLog(TypedDict):
    """Individual agent execution log entry"""
    agent_name: str
    timestamp: str
    input_summary: str
    output_summary: str
    execution_time_ms: float
    success: bool
    error_message: Optional[str]

class RetrievedContext(TypedDict):
    """
    A unified structure for holding retrieved context from any source.
    This structure is designed to be compatible with both vector search
    results and deep graph retrieval results.
    """
    source: str          # e.g., 'vector_search', 'deep_graph_retrieval', 'web_search'
    query: str           # The sub-query that prompted this retrieval
    uid: str             # A unique identifier for the retrieved item (e.g., chunk ID, URL)
    title: Optional[str] # The title of the document or section
    text: str            # The main content of the retrieved chunk
    metadata: Dict[str, Any] # Any other relevant metadata

class QualityMetrics(TypedDict):
    """Quality assessment metrics for responses"""
    context_sufficiency_score: float
    retrieval_relevance_score: float
    synthesis_quality_score: float
    total_sources_used: int
    fallback_methods_used: List[str]

class AgentState(TypedDict):
    """
    Complete state object for the LangGraph workflow.
    
    This maintains all state needed for the sophisticated agentic workflow
    while being compatible with LangGraph's state management system.
    """
    
    # === Core Inputs ===
    user_query: str  # The current query from the user
    context_payload: str  # Context from the conversation manager
    original_query: Optional[str] # The query that initiated the current agentic workflow
    # conversation_manager: Optional[object]  # Removed - not serializable for LangGraph
    
    # === Workflow Control ===
    current_step: Literal["triage", "planning", "research", "validation", "calculation", "placeholder", "synthesis", "memory_update", "finish", "error"]
    workflow_status: Literal["running", "completed", "failed", "retry"]
    retry_count: int
    max_retries: int
    
    # === Triage Results ===
    triage_classification: Optional[Literal["engage", "direct_retrieval", "clarify", "reject"]]
    triage_reasoning: Optional[str]
    triage_confidence: Optional[float]
    
    # === Planning Agent Results ===
    planning_classification: Optional[Literal["engage", "direct_retrieval", "clarify", "reject"]]
    planning_reasoning: Optional[str]
    research_plan: Optional[List[Dict[str, str]]] = Field(
        default_factory=list, 
        description="A list of sub-queries to research."
    )
    direct_answer: Optional[str]
    direct_retrieval_entity: Optional[Dict[str, str]]  # {entity_type, entity_id}
    
    # === Research Agent Results ===
    research_results: Optional[Dict[str, List[Dict[str, Any]]]]  # Maps sub_query to results
    sub_query_answers: Optional[List[Dict[str, str]]] = Field(
        default_factory=list,
        description="A list of answers to the sub-queries."
    )
    research_metadata: Optional[Dict[str, Any]]
    parallel_execution_log: Optional[List[Dict[str, Any]]]
    retrieval_quality_scores: Optional[Dict[str, float]]
    
    # === Validation Results ===
    research_validation_results: Optional[Dict[str, Any]]  # Research sufficiency assessment
    math_calculation_needed: Optional[bool]  # Whether math calculations are required
    validation_confidence: Optional[float]  # Confidence in validation results
    
    # === Calculation Results ===
    calculation_request: Optional[str]  # Code to execute for calculations
    calculation_results: Optional[Dict[str, Any]]  # Results from calculation execution
    calculation_attempts: Optional[int]  # Number of calculation attempts made
    calculation_success: Optional[bool]  # Whether calculations succeeded
    
    # === Placeholder Results ===
    placeholder_content: Optional[str]  # Content with placeholders for missing info
    enhancement_suggestions: Optional[List[str]]  # Suggestions for improving research
    
    # === Synthesis Results ===
    final_answer: Optional[str]
    synthesis_metadata: Optional[Dict[str, Any]]
    source_citations: Optional[List[str]]
    
    # === Error Handling ===
    error_state: Optional[Dict[str, Any]]
    error_recovery_attempts: Optional[List[str]]
    fallback_results: Optional[Dict[str, Any]]
    
    # === Execution Tracking ===
    execution_log: List[ExecutionLog]
    start_time: Optional[str]
    end_time: Optional[str]
    total_execution_time_ms: Optional[float]
    
    # === Quality Metrics ===
    quality_metrics: Optional[QualityMetrics]
    confidence_score: Optional[float]
    
    # === Memory Integration ===
    memory_update_required: bool
    memory_update_completed: bool
    conversation_updated: bool
    
    # === Debug Information ===
    debug_mode: bool
    intermediate_outputs: Optional[Dict[str, Any]]
    performance_metrics: Optional[Dict[str, Any]]
    cognitive_flow_messages: List[Dict[str, Any]]

    # === Mathematical Enhancement Metadata ===
    mathematical_metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Tracks mathematical content detection and enhancement throughout workflow"
    )

    retrieved_diagrams: Optional[List[Dict[str, Any]]] = Field(
        default_factory=list,
        description="A list of retrieved diagrams, including their processed image data and metadata."
    )

def create_initial_state(
    user_query: str, 
    context_payload: str, 
    conversation_manager=None,
    debug_mode: bool = False
) -> AgentState:
    """
    Creates the initial state for a new workflow execution.
    
    Args:
        user_query: The user's input question
        context_payload: Context from conversation manager
        conversation_manager: ConversationManager instance
        debug_mode: Whether to enable debug logging
        
    Returns:
        Initial AgentState for workflow execution
    """
    return AgentState(
        # Core inputs
        user_query=user_query,
        context_payload=context_payload,
        original_query=user_query, # At the start, user_query is the original_query
        # conversation_manager=conversation_manager,  # Removed - not serializable
        
        # Workflow control
        current_step="triage",
        workflow_status="running",
        retry_count=0,
        max_retries=3,
        
        # Initialize optional fields as None
        triage_classification=None,
        triage_reasoning=None,
        triage_confidence=None,
        planning_classification=None,
        planning_reasoning=None,
        research_plan=None,
        direct_answer=None,
        direct_retrieval_entity=None,
        research_results=None,
        sub_query_answers=None,
        research_metadata=None,
        parallel_execution_log=None,
        retrieval_quality_scores=None,
        
        # Initialize validation and calculation fields
        research_validation_results=None,
        math_calculation_needed=None,
        validation_confidence=None,
        calculation_request=None,
        calculation_results=None,
        calculation_attempts=0,
        calculation_success=None,
        placeholder_content=None,
        enhancement_suggestions=None,
        
        final_answer=None,
        synthesis_metadata=None,
        source_citations=None,
        error_state=None,
        error_recovery_attempts=None,
        fallback_results=None,
        quality_metrics=None,
        confidence_score=None,
        
        # Execution tracking
        execution_log=[],
        start_time=datetime.now().isoformat(),
        end_time=None,
        total_execution_time_ms=None,
        
        # Memory
        memory_update_required=True,
        memory_update_completed=False,
        conversation_updated=False,
        
        # Debug
        debug_mode=debug_mode,
        intermediate_outputs={} if debug_mode else None,
        performance_metrics={} if debug_mode else None,
        mathematical_metadata={} if debug_mode else None,
        cognitive_flow_messages=[]
    )

def log_agent_execution(
    state: AgentState, 
    agent_name: str, 
    input_data: Any, 
    output_data: Any,
    execution_time_ms: float,
    success: bool = True,
    error_message: Optional[str] = None
) -> AgentState:
    """
    Logs an agent execution to the state.
    
    Args:
        state: Current workflow state
        agent_name: Name of the executed agent
        input_data: Input data to the agent (will be summarized)
        output_data: Output data from the agent (will be summarized)
        execution_time_ms: Execution time in milliseconds
        success: Whether execution was successful
        error_message: Error message if failed
        
    Returns:
        Updated state with execution log entry
    """
    execution_entry = ExecutionLog(
        agent_name=agent_name,
        timestamp=datetime.now().isoformat(),
        input_summary=_summarize_data(input_data),
        output_summary=_summarize_data(output_data),
        execution_time_ms=execution_time_ms,
        success=success,
        error_message=error_message
    )
    
    # Create new execution log with the entry added
    new_execution_log = state["execution_log"] + [execution_entry]
    
    # Return updated state
    updated_state = state.copy()
    updated_state["execution_log"] = new_execution_log
    
    return updated_state

def _summarize_data(data: Any, max_length: int = 150) -> str:
    """
    Creates a summary of data for logging purposes.
    
    Args:
        data: Data to summarize
        max_length: Maximum length of summary
        
    Returns:
        String summary of the data
    """
    if data is None:
        return "None"
    
    if isinstance(data, str):
        return data[:max_length] + "..." if len(data) > max_length else data
    
    if isinstance(data, dict):
        keys = list(data.keys())[:3]  # First 3 keys
        summary = f"Dict with keys: {keys}"
        if len(data) > 3:
            summary += f" (+{len(data) - 3} more)"
        return summary
    
    if isinstance(data, list):
        return f"List with {len(data)} items"
    
    return str(data)[:max_length]

def is_workflow_complete(state: AgentState) -> bool:
    """
    Checks if the workflow has reached a completion state.
    
    Args:
        state: Current workflow state
        
    Returns:
        True if workflow is complete
    """
    return (
        state["workflow_status"] in ["completed", "failed"] or
        state["current_step"] == "finish" or
        state.get("final_answer") is not None or
        state.get("direct_answer") is not None
    )

def should_retry(state: AgentState) -> bool:
    """
    Determines if the workflow should retry after an error.
    
    Args:
        state: Current workflow state
        
    Returns:
        True if should retry
    """
    return (
        state.get("error_state") is not None and
        state["retry_count"] < state["max_retries"] and
        state["workflow_status"] != "failed"
    ) 