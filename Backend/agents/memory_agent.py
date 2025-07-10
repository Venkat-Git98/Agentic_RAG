"""
Memory Agent for LangGraph workflow.

This agent integrates with the existing ConversationManager to handle
memory updates and conversation state management at the end of successful
workflow executions.
"""

import sys
import os
from typing import Dict, Any, List
from datetime import datetime

# Add parent directories to path for imports
from .base_agent import BaseLangGraphAgent
from state import AgentState

class MemoryAgent(BaseLangGraphAgent):
    """
    Memory Agent for conversation state management and memory updates.
    
    This agent handles the integration with the ConversationManager to:
    - Update conversation history with the final response
    - Trigger memory consolidation if needed
    - Ensure conversation state persistence
    - Finalize workflow execution
    """
    
    def __init__(self):
        """Initialize the Memory Agent with lightweight processing."""
        # Use Tier 2 model for lightweight memory operations
        super().__init__(model_tier="tier_2", agent_name="MemoryAgent")
        
        self.logger.info("Memory Agent initialized successfully")
    
    async def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute memory update and conversation management.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dictionary containing memory update results
        """
        # Get conversation manager from workflow (stored separately, not in state)
        conversation_manager = getattr(self, '_workflow_conversation_manager', None)
        final_answer = state.get("final_answer")
        direct_answer = state.get("direct_answer")
        user_query = state.get("user_query", "")
        
        # Determine the response to store
        response_to_store = final_answer or direct_answer or "No response generated."
        
        if not conversation_manager:
            self.logger.warning("No conversation manager provided, skipping memory update")
            return {
                "memory_update_completed": False,
                "conversation_updated": False,
                "current_step": "finish",
                "workflow_status": "completed"
            }
        
        response_preview = response_to_store[:100] if response_to_store else "No response"
        self.logger.info(f"Updating conversation memory with response: {response_preview}...")
        
        try:
            # Update conversation manager with the final exchange
            conversation_manager.add_message("user", user_query)
            conversation_manager.add_message("assistant", response_to_store)
            
            # Calculate total execution time if available
            execution_time = self._calculate_execution_time(state)
            
            self.logger.info("Memory update completed successfully")
            
            return {
                "memory_update_completed": True,
                "conversation_updated": True,
                "total_execution_time_ms": execution_time,
                "end_time": datetime.now().isoformat(),
                "current_step": "finish",
                "workflow_status": "completed"
            }
            
        except Exception as e:
            self.logger.error(f"Error updating conversation memory: {e}")
            return {
                "memory_update_completed": False,
                "conversation_updated": False,
                "error_state": {
                    "agent": self.agent_name,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "timestamp": datetime.now().isoformat()
                },
                "current_step": "finish",
                "workflow_status": "completed"  # Complete anyway, memory error shouldn't fail workflow
            }
    
    def _calculate_execution_time(self, state: AgentState) -> float:
        """
        Calculates total execution time from start to finish.
        
        Args:
            state: Current workflow state
            
        Returns:
            Total execution time in milliseconds
        """
        start_time = state.get("start_time")
        if not start_time:
            return 0.0
        
        try:
            start_dt = datetime.fromisoformat(start_time)
            end_dt = datetime.now()
            delta = end_dt - start_dt
            return delta.total_seconds() * 1000  # Convert to milliseconds
        except (ValueError, TypeError):
            self.logger.warning("Could not parse start_time for execution time calculation")
            return 0.0
    
    def _validate_agent_specific_state(self, state: AgentState) -> None:
        """
        Validates memory agent specific state requirements.
        
        Args:
            state: State to validate
        """
        # Memory agent is quite flexible - it can work with any state
        # The main requirement is that we have some kind of response to store
        has_response = (
            state.get("final_answer") or 
            state.get("direct_answer") or 
            state.get("user_query")
        )
        
        if not has_response:
            self.logger.warning("No response or query found for memory update")
    
    def _apply_agent_specific_updates(self, state: AgentState, output_data: Dict[str, Any]) -> AgentState:
        """
        Applies memory-specific updates to the state.
        
        This method ensures that intermediate outputs are correctly logged without
        overwriting previous logs from other agents.
        """
        updated_state = state.copy()
        
        # Ensure intermediate_outputs is a list
        if "intermediate_outputs" not in updated_state or not isinstance(updated_state["intermediate_outputs"], list):
            updated_state["intermediate_outputs"] = []

        # Log the memory update
        log_entry = {
            "agent": self.agent_name,
            "output": {
                "memory_updated": output_data.get("memory_updated", False),
                "summary_length": len(output_data.get("conversation_summary", ""))
            },
            "timestamp": datetime.now().isoformat()
        }
        
        updated_state["intermediate_outputs"].append(log_entry)

        return updated_state

class EnhancedMemoryAgent(MemoryAgent):
    """
    Enhanced Memory Agent with additional conversation analytics.
    
    This version includes extra features for analyzing conversation patterns
    and providing insights about the workflow execution.
    """
    
    def __init__(self):
        """Initialize the Enhanced Memory Agent."""
        super().__init__()
        self.agent_name = "EnhancedMemoryAgent"
    
    async def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        Enhanced execution with conversation analytics.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dictionary containing enhanced memory results
        """
        # Execute base memory operations
        result = await super().execute(state)
        
        # Add conversation analytics
        analytics = self._generate_conversation_analytics(state)
        result["conversation_analytics"] = analytics
        
        # Add workflow performance insights
        performance_insights = self._generate_performance_insights(state)
        result["performance_insights"] = performance_insights
        
        return result
    
    def _generate_conversation_analytics(self, state: AgentState) -> Dict[str, Any]:
        """
        Generates analytics about the conversation and workflow.
        
        Args:
            state: Current workflow state
            
        Returns:
            Conversation analytics dictionary
        """
        analytics = {
            "query_complexity": self._assess_query_complexity(state),
            "response_quality": self._assess_response_quality(state),
            "workflow_path": self._trace_workflow_path(state),
            "resource_utilization": self._assess_resource_utilization(state)
        }
        
        return analytics
    
    def _generate_performance_insights(self, state: AgentState) -> Dict[str, Any]:
        """
        Generates performance insights from the workflow execution.
        
        Args:
            state: Current workflow state
            
        Returns:
            Performance insights dictionary
        """
        execution_log = state.get("execution_log", [])
        
        if not execution_log:
            return {"insights": "No execution data available"}
        
        # Calculate agent performance metrics
        agent_times = {}
        for log_entry in execution_log:
            agent_name = log_entry.get("agent_name", "unknown")
            exec_time = log_entry.get("execution_time_ms", 0.0)
            
            if agent_name in agent_times:
                agent_times[agent_name].append(exec_time)
            else:
                agent_times[agent_name] = [exec_time]
        
        # Generate insights
        insights = {
            "total_agents_executed": len(agent_times),
            "agent_performance": {
                agent: {
                    "total_time_ms": sum(times),
                    "average_time_ms": sum(times) / len(times),
                    "execution_count": len(times)
                }
                for agent, times in agent_times.items()
            },
            "bottlenecks": self._identify_bottlenecks(agent_times),
            "success_rate": self._calculate_success_rate(execution_log)
        }
        
        return insights
    
    def _assess_query_complexity(self, state: AgentState) -> str:
        """Assesses the complexity of the user query."""
        user_query = state.get("user_query", "")
        research_plan = state.get("research_plan", [])
        
        if len(research_plan) > 3:
            return "high"
        elif len(research_plan) > 1:
            return "medium"
        elif state.get("planning_classification") == "direct_retrieval":
            return "low"
        else:
            return "medium"
    
    def _assess_response_quality(self, state: AgentState) -> str:
        """Assesses the quality of the generated response."""
        confidence_score = state.get("confidence_score", 0.0)
        
        if confidence_score >= 0.8:
            return "high"
        elif confidence_score >= 0.6:
            return "medium"
        else:
            return "low"
    
    def _trace_workflow_path(self, state: AgentState) -> List[str]:
        """Traces the path taken through the workflow."""
        execution_log = state.get("execution_log", [])
        return [log_entry.get("agent_name", "unknown") for log_entry in execution_log]
    
    def _assess_resource_utilization(self, state: AgentState) -> Dict[str, Any]:
        """Assesses how resources were utilized during execution."""
        quality_metrics = state.get("quality_metrics", {})
        research_metadata = state.get("research_metadata", {})
        
        return {
            "sources_accessed": quality_metrics.get("total_sources_used", 0),
            "fallback_methods": len(quality_metrics.get("fallback_methods_used", [])),
            "retrieval_efficiency": quality_metrics.get("retrieval_relevance_score", 0.0),
            "research_quality": research_metadata.get("research_quality", "unknown")
        }
    
    def _identify_bottlenecks(self, agent_times: Dict[str, List[float]]) -> List[str]:
        """Identifies potential bottlenecks in the workflow."""
        bottlenecks = []
        
        for agent, times in agent_times.items():
            avg_time = sum(times) / len(times)
            if avg_time > 5000:  # More than 5 seconds
                bottlenecks.append(f"{agent} (avg: {avg_time:.0f}ms)")
        
        return bottlenecks
    
    def _calculate_success_rate(self, execution_log: List[Dict[str, Any]]) -> float:
        """Calculates the success rate of agent executions."""
        if not execution_log:
            return 0.0
        
        successful_executions = len([log for log in execution_log if log.get("success", False)])
        return successful_executions / len(execution_log) 