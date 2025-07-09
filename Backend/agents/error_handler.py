"""
Error Handler Agent for LangGraph workflow.

This agent handles error recovery, retry logic, and graceful degradation
when agents encounter failures during workflow execution.
"""

import sys
import os
from typing import Dict, Any, List
from datetime import datetime

# Add parent directories to path for imports
from .base_agent import BaseLangGraphAgent
from state import AgentState, should_retry

class ErrorHandler(BaseLangGraphAgent):
    """
    Error Handler Agent for workflow error recovery and graceful degradation.
    
    This agent handles:
    - Error analysis and classification
    - Retry logic for recoverable errors
    - Graceful degradation strategies
    - Error reporting and logging
    - Fallback response generation
    """
    
    def __init__(self):
        """Initialize the Error Handler with Tier 2 model for efficient processing."""
        super().__init__(model_tier="tier_2", agent_name="ErrorHandler")
        
        # Error classification patterns
        self.recoverable_errors = [
            "timeout", "connection", "rate_limit", "temporary", "network"
        ]
        
        self.non_recoverable_errors = [
            "authentication", "permission", "invalid_config", "missing_data"
        ]
        
        self.logger.info("Error Handler initialized successfully")
    
    async def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute error handling and recovery logic.
        
        Args:
            state: Current workflow state with error information
            
        Returns:
            Dictionary containing error handling results
        """
        error_state = state.get("error_state", {})
        retry_count = state.get("retry_count", 0)
        max_retries = state.get("max_retries", 3)
        
        if not error_state:
            self.logger.warning("Error handler called but no error_state found")
            return {
                "error_handled": False,
                "recovery_action": "none",
                "current_step": "finish",
                "workflow_status": "completed"
            }
        
        self.logger.info(f"Handling error: {error_state.get('error_type', 'unknown')}")
        
        # Analyze the error
        error_analysis = await self._analyze_error(error_state, state)
        
        # Determine recovery strategy
        recovery_strategy = await self._determine_recovery_strategy(error_analysis, state)
        
        # Execute recovery if possible
        return await self._execute_recovery(recovery_strategy, error_analysis, state)
    
    async def _analyze_error(self, error_state: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """
        Analyzes the error to determine its nature and recoverability.
        
        Args:
            error_state: Error information from the failed agent
            state: Current workflow state
            
        Returns:
            Error analysis results
        """
        error_type = error_state.get("error_type", "unknown")
        error_message = error_state.get("error_message", "")
        failed_agent = error_state.get("agent", "unknown")
        
        # Classify error severity and recoverability
        is_recoverable = self._is_error_recoverable(error_type, error_message)
        severity = self._assess_error_severity(error_type, failed_agent, state)
        
        # Determine root cause
        root_cause = self._identify_root_cause(error_type, error_message, failed_agent)
        
        analysis = {
            "error_type": error_type,
            "error_message": error_message,
            "failed_agent": failed_agent,
            "is_recoverable": is_recoverable,
            "severity": severity,
            "root_cause": root_cause,
            "retry_recommended": is_recoverable and state.get("retry_count", 0) < state.get("max_retries", 3)
        }
        
        self.logger.info(f"Error analysis: {analysis}")
        return analysis
    
    async def _determine_recovery_strategy(self, error_analysis: Dict[str, Any], state: AgentState) -> str:
        """
        Determines the best recovery strategy based on error analysis.
        
        Args:
            error_analysis: Results from error analysis
            state: Current workflow state
            
        Returns:
            Recovery strategy name
        """
        if not error_analysis["is_recoverable"]:
            return "graceful_degradation"
        
        if error_analysis["retry_recommended"]:
            return "retry"
        
        # Check for alternative strategies based on failed agent
        failed_agent = error_analysis["failed_agent"]
        
        if "planning" in failed_agent.lower():
            return "planning_fallback"
        elif "research" in failed_agent.lower():
            return "research_fallback"
        elif "synthesis" in failed_agent.lower():
            return "synthesis_fallback"
        else:
            return "graceful_degradation"
    
    async def _execute_recovery(self, strategy: str, error_analysis: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """
        Executes the determined recovery strategy.
        
        Args:
            strategy: Recovery strategy to execute
            error_analysis: Error analysis results
            state: Current workflow state
            
        Returns:
            Recovery execution results
        """
        self.logger.info(f"Executing recovery strategy: {strategy}")
        
        if strategy == "retry":
            return await self._execute_retry(error_analysis, state)
        elif strategy == "planning_fallback":
            return await self._execute_planning_fallback(error_analysis, state)
        elif strategy == "research_fallback":
            return await self._execute_research_fallback(error_analysis, state)
        elif strategy == "synthesis_fallback":
            return await self._execute_synthesis_fallback(error_analysis, state)
        else:  # graceful_degradation
            return await self._execute_graceful_degradation(error_analysis, state)
    
    async def _execute_retry(self, error_analysis: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Executes retry strategy by resetting to previous step."""
        failed_agent = error_analysis["failed_agent"]
        
        # Determine which step to retry
        if "triage" in failed_agent.lower():
            retry_step = "triage"
        elif "planning" in failed_agent.lower():
            retry_step = "planning"
        elif "research" in failed_agent.lower():
            retry_step = "research"
        elif "synthesis" in failed_agent.lower():
            retry_step = "synthesis"
        else:
            retry_step = "planning"  # Default fallback
        
        return {
            "error_handled": True,
            "recovery_action": "retry",
            "retry_step": retry_step,
            "retry_count": state.get("retry_count", 0) + 1,
            "current_step": retry_step,
            "workflow_status": "running",
            "error_state": None  # Clear error state for retry
        }
    
    async def _execute_planning_fallback(self, error_analysis: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Executes planning fallback by creating a simple research plan."""
        user_query = state.get("user_query", "")
        
        # Create a basic fallback plan
        fallback_plan = [{
            "sub_query": user_query,
            "hyde_document": f"Answer the following question about the Virginia Building Code: {user_query}"
        }]
        
        return {
            "error_handled": True,
            "recovery_action": "planning_fallback",
            "research_plan": fallback_plan,
            "planning_classification": "engage",
            "planning_reasoning": "Fallback plan generated due to planning agent error",
            "current_step": "research",
            "workflow_status": "running"
        }
    
    async def _execute_research_fallback(self, error_analysis: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Executes research fallback by creating minimal sub-answers."""
        user_query = state.get("user_query", "")
        
        # Create minimal fallback sub-answers
        fallback_answers = [{
            "sub_query": user_query,
            "answer": f"I encountered an issue while researching your question about: {user_query}. Please try rephrasing your question or contact support for assistance.",
            "sources_used": [],
            "fallback_method": "error_recovery"
        }]
        
        return {
            "error_handled": True,
            "recovery_action": "research_fallback",
            "sub_query_answers": fallback_answers,
            "research_metadata": {
                "total_sub_queries": 1,
                "successful_queries": 0,
                "fallback_methods_used": ["error_recovery"]
            },
            "current_step": "synthesis",
            "workflow_status": "running"
        }
    
    async def _execute_synthesis_fallback(self, error_analysis: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Executes synthesis fallback by creating a basic response."""
        user_query = state.get("user_query", "")
        sub_query_answers = state.get("sub_query_answers", [])
        
        # Create a basic fallback response
        if sub_query_answers:
            # Try to combine available answers
            combined_text = "\n\n".join([ans.get("answer", "") for ans in sub_query_answers if ans.get("answer")])
            fallback_answer = f"Based on the available information:\n\n{combined_text}\n\nNote: This response was generated using fallback synthesis due to a processing error."
        else:
            fallback_answer = f"I apologize, but I encountered an error while processing your question: {user_query}. Please try rephrasing your question or contact support for assistance."
        
        return {
            "error_handled": True,
            "recovery_action": "synthesis_fallback",
            "final_answer": fallback_answer,
            "synthesis_metadata": {
                "answer_length_chars": len(fallback_answer),
                "fallback_synthesis": True
            },
            "confidence_score": 0.3,  # Low confidence for fallback
            "current_step": "memory_update",
            "workflow_status": "running"
        }
    
    async def _execute_graceful_degradation(self, error_analysis: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """Executes graceful degradation by providing a helpful error message."""
        user_query = state.get("user_query", "")
        error_type = error_analysis.get("error_type", "unknown")
        
        # Create an informative error response
        degradation_message = self._generate_degradation_message(user_query, error_type, error_analysis)
        
        return {
            "error_handled": True,
            "recovery_action": "graceful_degradation",
            "direct_answer": degradation_message,
            "error_reported": True,
            "current_step": "finish",
            "workflow_status": "completed"
        }
    
    def _is_error_recoverable(self, error_type: str, error_message: str) -> bool:
        """Determines if an error is recoverable based on type and message."""
        error_text = f"{error_type} {error_message}".lower()
        
        # Check for recoverable patterns
        for pattern in self.recoverable_errors:
            if pattern in error_text:
                return True
        
        # Check for non-recoverable patterns
        for pattern in self.non_recoverable_errors:
            if pattern in error_text:
                return False
        
        # Default to recoverable for unknown errors
        return True
    
    def _assess_error_severity(self, error_type: str, failed_agent: str, state: AgentState) -> str:
        """Assesses the severity of an error."""
        # Critical errors that completely break the workflow
        if error_type in ["AuthenticationError", "ConfigurationError"]:
            return "critical"
        
        # High severity for core agents
        if failed_agent in ["PlanningAgent", "ResearchOrchestrator"]:
            return "high"
        
        # Medium severity for supporting agents
        if failed_agent in ["SynthesisAgent", "MemoryAgent"]:
            return "medium"
        
        # Low severity for utility agents
        return "low"
    
    def _identify_root_cause(self, error_type: str, error_message: str, failed_agent: str) -> str:
        """Identifies the likely root cause of the error."""
        error_text = f"{error_type} {error_message}".lower()
        
        if "timeout" in error_text or "connection" in error_text:
            return "network_issue"
        elif "rate" in error_text or "limit" in error_text:
            return "rate_limiting"
        elif "authentication" in error_text or "unauthorized" in error_text:
            return "authentication_failure"
        elif "not found" in error_text or "missing" in error_text:
            return "missing_resource"
        elif "invalid" in error_text or "malformed" in error_text:
            return "data_validation"
        elif "memory" in error_text or "resource" in error_text:
            return "resource_exhaustion"
        else:
            return "unknown"
    
    def _generate_degradation_message(self, user_query: str, error_type: str, error_analysis: Dict[str, Any]) -> str:
        """Generates a helpful error message for graceful degradation."""
        root_cause = error_analysis.get("root_cause", "unknown")
        
        base_message = f"I apologize, but I encountered an issue while processing your question: \"{user_query}\""
        
        if root_cause == "network_issue":
            return f"{base_message}\n\nThis appears to be a temporary network connectivity issue. Please try again in a few moments."
        elif root_cause == "rate_limiting":
            return f"{base_message}\n\nI'm currently experiencing high demand. Please wait a moment and try again."
        elif root_cause == "authentication_failure":
            return f"{base_message}\n\nThere seems to be a configuration issue. Please contact support for assistance."
        elif root_cause == "missing_resource":
            return f"{base_message}\n\nSome required resources are currently unavailable. Please try rephrasing your question or contact support."
        else:
            return f"{base_message}\n\nPlease try rephrasing your question or contact support if the issue persists."
    
    def _validate_agent_specific_state(self, state: AgentState) -> None:
        """Validates error handler specific state requirements."""
        # Error handler should have some kind of error to process
        if not state.get("error_state"):
            self.logger.warning("Error handler called without error_state")
    
    def _apply_agent_specific_updates(self, state: AgentState, output_data: Dict[str, Any]) -> AgentState:
        """Applies error handler specific state updates."""
        updated_state = state.copy()
        updated_state.update(output_data)

        # Log error handling details
        if "intermediate_outputs" in updated_state and updated_state["intermediate_outputs"] is not None:
            log_entry = {
                "step": "error_handling",
                "agent": self.agent_name,
                "failed_agent": updated_state.get("error_state", {}).get("agent"),
                "recovery_strategy": output_data.get("recovery_action"),
                "timestamp": datetime.now().isoformat()
            }
            updated_state["intermediate_outputs"].append(log_entry)
            
        return updated_state 