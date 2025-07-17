"""
Centralized State Keys for the LangGraph Agentic AI System.

This module defines all dictionary keys used in the AgentState TypedDict
and for other state management purposes. Using these constants across the
application prevents typos and ensures consistency.
"""

# --- Core Inputs & Workflow Control ---
USER_QUERY = "user_query"
CONTEXT_PAYLOAD = "context_payload"
ORIGINAL_QUERY = "original_query"
CURRENT_STEP = "current_step"
WORKFLOW_STATUS = "workflow_status"

# --- Triage Agent State ---
TRIAGE_CLASSIFICATION = "triage_classification"
TRIAGE_REASONING = "triage_reasoning"
TRIAGE_CONFIDENCE = "triage_confidence"
IS_FOLLOW_UP = "is_follow_up"
REWRITTEN_QUERY = "rewritten_query"

# --- Planning Agent State ---
PLANNING_CLASSIFICATION = "planning_classification"
PLANNING_REASONING = "planning_reasoning"
RESEARCH_PLAN = "research_plan"
DIRECT_ANSWER = "direct_answer"
CONTEXTUAL_ANSWER = "contextual_answer"

# --- Research & Synthesis State ---
SUB_QUERY_ANSWERS = "sub_query_answers"
FINAL_ANSWER = "final_answer"
SYNTHESIS_METADATA = "synthesis_metadata"
SOURCE_CITATIONS = "source_citations"
CONFIDENCE_SCORE = "confidence_score"

# --- Validation & Calculation State ---
RESEARCH_VALIDATION_RESULTS = "research_validation_results"
MATH_CALCULATION_NEEDED = "math_calculation_needed"
CALCULATION_RESULTS = "calculation_results"
CALCULATION_EXECUTION_SUCCESS = "calculation_execution_success"

# --- Error & Recovery State ---
ERROR_STATE = "error_state"
RETRY_COUNT = "retry_count"
MAX_RETRIES = "max_retries"
RECOVERY_ACTION = "recovery_action"
RETRY_STEP = "retry_step"

# --- Memory Agent State ---
MEMORY_UPDATE_COMPLETED = "memory_update_completed"

# --- Intermediate & Quality Metrics ---
INTERMEDIATE_OUTPUTS = "intermediate_outputs"
QUALITY_METRICS = "quality_metrics" 