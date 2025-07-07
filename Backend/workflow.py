"""
Main LangGraph Workflow for Agentic AI System.

This module implements the complete LangGraph-based workflow that orchestrates
all agents in the sophisticated agentic AI pipeline, preserving all the advanced
logic from the original ReAct system while leveraging LangGraph's capabilities.
"""

import sys
import os
from typing import Dict, Any, List, Literal
import logging
from datetime import datetime
import re

# Add parent directories to path for imports
# LangGraph imports
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# Local imports
from state import AgentState, create_initial_state, is_workflow_complete, should_retry
from agents import (
    RouterAgent, PlanningAgent, ResearchOrchestrator, 
    SynthesisAgent, MemoryAgent, ErrorHandler
)

class AgenticWorkflow:
    """
    Main LangGraph workflow for the sophisticated agentic AI system.
    
    This workflow preserves all the advanced features from the original system:
    - Sophisticated triage and planning
    - Parallel research with fallback systems
    - Advanced synthesis with quality metrics
    - Comprehensive error handling and recovery
    - Memory management and conversation integration
    """
    
    def __init__(self, debug_mode: bool = False):
        """
        Initialize the LangGraph workflow.
        
        Args:
            debug_mode: Whether to enable debug logging and intermediate outputs
        """
        self.debug_mode = debug_mode
        self.logger = logging.getLogger("AgenticWorkflow")
        self.conversation_manager = None  # Store conversation manager separately
        
        # Initialize agents
        self._initialize_agents()
        
        # Build the workflow graph
        self.workflow = self._build_workflow_graph()
        
        # Compile the workflow
        self.app = self._compile_workflow()
        
        self.logger.info(f"Agentic workflow initialized (debug={self.debug_mode})")
    
    def _initialize_agents(self):
        """Initialize all agents for the workflow."""
        # Import Enhanced agents (now the only agents)
        from .agents.planning_agent import EnhancedPlanningAgent
        from .agents.research_orchestrator import EnhancedResearchOrchestrator
        from .agents.synthesis_agent import EnhancedSynthesisAgent
        from .agents.memory_agent import EnhancedMemoryAgent
        
        # FIXED: Import thinking agents instead of missing regular agents
        from .thinking_agents.thinking_validation_agent import ThinkingValidationAgent
        from .thinking_agents.thinking_calculation_executor import ThinkingCalculationExecutor
        from .thinking_agents.thinking_placeholder_handler import ThinkingPlaceholderHandler
        from .thinking_logger import ThinkingMode
        
        # Initialize all agents with Enhanced versions
        self.router_agent = RouterAgent()
        self.planning_agent = EnhancedPlanningAgent()
        self.research_agent = EnhancedResearchOrchestrator()
        self.synthesis_agent = EnhancedSynthesisAgent()
        self.memory_agent = EnhancedMemoryAgent()
        self.error_handler = ErrorHandler()
        
        # FIXED: Initialize thinking agents with proper thinking mode
        self.validation_agent = ThinkingValidationAgent(thinking_mode=ThinkingMode.SIMPLE)
        self.calculation_executor = ThinkingCalculationExecutor(thinking_mode=ThinkingMode.SIMPLE)
        self.placeholder_handler = ThinkingPlaceholderHandler(thinking_mode=ThinkingMode.SIMPLE)
    
    def _summary_check(self, state: AgentState) -> str:
        """
        Checks if the user query is a summary request and routes accordingly.
        This acts as a pre-router to handle this specific, problematic case.
        """
        user_query = state.get("user_query", "").lower()
        if re.search(r'\b(summarize|summary of)\b', user_query) and "chapter" in user_query:
            self.logger.info("Summary request detected, bypassing planner and routing directly to research.")
            # This logic was flawed. It needs to create a research plan and pass it in the state.
            chapter_match = re.search(r'chapter\s+(\d+)', user_query)
            chapter_number = chapter_match.group(1) if chapter_match else "the specified chapter"
            
            research_plan = [
                {"sub_query": f"Retrieve all subsections and content for Chapter {chapter_number} to create a summary."},
                {"sub_query": f"Synthesize the retrieved subsections of Chapter {chapter_number} into a comprehensive summary."}
            ]
            state['research_plan'] = research_plan
            return "research"
        return "router"
    
    def _build_workflow_graph(self) -> StateGraph:
        """
        Builds the LangGraph workflow graph with all nodes and edges.
        
        Returns:
            Configured StateGraph for the workflow
        """
        # Create the state graph
        workflow = StateGraph(AgentState)
        
        # Add all agent nodes
        workflow.add_node("summary_check", self._summary_check)
        workflow.add_node("router", self.router_agent)
        workflow.add_node("planning", self.planning_agent)
        workflow.add_node("research", self.research_agent)
        
        # NEW: Add validation and calculation nodes
        workflow.add_node("validation", self.validation_agent)
        workflow.add_node("calculation", self.calculation_executor)
        workflow.add_node("placeholder", self.placeholder_handler)
        
        workflow.add_node("synthesis", self.synthesis_agent)
        workflow.add_node("memory_update", self.memory_agent)
        workflow.add_node("error_handler", self.error_handler)
        
        # Set entry point
        workflow.set_entry_point("summary_check")
        
        # CORRECTED conditional edge
        workflow.add_conditional_edges(
            "summary_check",
            self._summary_check,
            {
                "research": "research",
                "router": "router"
            }
        )
        
        # Add conditional edges based on workflow logic
        workflow.add_conditional_edges(
            "router",
            self._route_after_router,
            {
                "planning": "planning",
                "finish": END,
                "error": "error_handler"
            }
        )
        
        workflow.add_conditional_edges(
            "planning",
            self._route_after_planning,
            {
                "research": "research",
                "synthesis": "synthesis",  # Route for direct retrieval
                "finish": END,
                "error": "error_handler"
            }
        )
        
        workflow.add_conditional_edges(
            "research",
            self._route_after_research,
            {
                "validation": "validation",
                "error": "error_handler"
            }
        )
        
        # NEW: Add validation routing
        workflow.add_conditional_edges(
            "validation",
            self._route_after_validation,
            {
                "calculation": "calculation",
                "placeholder": "placeholder", 
                "synthesis": "synthesis",
                "error": "error_handler"
            }
        )
        
        # NEW: Add calculation routing
        workflow.add_conditional_edges(
            "calculation",
            self._route_after_calculation,
            {
                "synthesis": "synthesis",
                "error": "error_handler"
            }
        )
        
        # NEW: Add placeholder routing
        workflow.add_conditional_edges(
            "placeholder",
            self._route_after_placeholder,
            {
                "synthesis": "synthesis",
                "error": "error_handler"
            }
        )
        
        workflow.add_conditional_edges(
            "synthesis",
            self._route_after_synthesis,
            {
                "memory_update": "memory_update",
                "error": "error_handler"
            }
        )
        
        workflow.add_conditional_edges(
            "memory_update",
            self._route_after_memory,
            {
                "finish": END,
                "error": "error_handler"
            }
        )
        
        workflow.add_conditional_edges(
            "error_handler",
            self._route_after_error,
            {
                "triage": "triage",
                "planning": "planning",
                "research": "research",
                "validation": "validation",
                "calculation": "calculation", 
                "placeholder": "placeholder",
                "synthesis": "synthesis",
                "finish": END
            }
        )
        
        return workflow
    
    def _compile_workflow(self):
        """
        Compiles the workflow with memory management.
        
        Returns:
            Compiled workflow application
        """
        # Add memory saver for conversation persistence
        memory = MemorySaver()
        
        # Compile the workflow
        app = self.workflow.compile(
            checkpointer=memory,
            debug=self.debug_mode
        )
        
        return app
    
    # Routing functions for conditional edges
    
    def _route_after_router(self, state: AgentState) -> Literal["planning", "finish", "error"]:
        """Routes workflow after the router step."""
        if state.get("error_state"):
            return "error"
        
        classification = state.get("routing_classification")
        
        if classification == "clarification":
            # TODO: Add logic to actually ask the user the clarifying question
            return "finish"
        elif classification == "direct_retrieval":
            # The planning agent will handle the direct retrieval
            return "planning"
        else: # research
            return "planning"
    
    def _route_after_planning(self, state: AgentState) -> Literal["research", "synthesis", "finish", "error"]:
        """Routes workflow after planning step."""
        if state.get("error_state"):
            return "error"
        
        planning_classification = state.get("planning_classification")
        
        if planning_classification == "direct_retrieval":
            # If context was retrieved directly, go to synthesis
            if state.get("retrieved_context"):
                return "synthesis"
            else:
                # This case should ideally not happen if retrieval is successful
                return "finish" 
        elif planning_classification == "engage":
            return "research"
        else:
            # For "clarify" or other unhandled cases
            return "finish"
    
    def _route_after_research(self, state: AgentState) -> Literal["validation", "error"]:
        """Routes workflow after research step."""
        if state.get("error_state"):
            return "error"
        
        return "validation"  # Always proceed to validation after research
    
    # NEW: Validation and calculation routing methods
    
    def _route_after_validation(self, state: AgentState) -> Literal["calculation", "placeholder", "synthesis", "error"]:
        """Routes workflow after validation step."""
        if state.get("error_state"):
            return "error"
        
        validation_result = state.get("validation_result", "synthesis") # Default to synthesis
        
        if validation_result == "calculation_needed":
            return "calculation"
        elif validation_result == "placeholder_needed":
            return "placeholder"
        elif validation_result == "synthesis":
            return "synthesis"
        else:
            # Fallback in case of unexpected validation result
            self.logger.warning(f"Unexpected validation result '{validation_result}', routing to synthesis.")
            return "synthesis"
    
    def _route_after_calculation(self, state: AgentState) -> Literal["synthesis", "error"]:
        """Routes workflow after calculation step."""
        if state.get("error_state"):
            return "error"
        
        return "synthesis"  # Always proceed to synthesis after calculation
    
    def _route_after_placeholder(self, state: AgentState) -> Literal["synthesis", "error"]:
        """Routes workflow after placeholder handling step."""
        if state.get("error_state"):
            return "error"
        
        return "synthesis"  # Proceed to synthesis with placeholder content
    
    def _route_after_synthesis(self, state: AgentState) -> Literal["memory_update", "error"]:
        """Routes workflow after synthesis step."""
        if state.get("error_state"):
            return "error"
        
        return "memory_update"  # Always update memory after synthesis
    
    def _route_after_memory(self, state: AgentState) -> Literal["finish", "error"]:
        """Routes workflow after memory update step."""
        if state.get("error_state"):
            return "error"
        
        return "finish"  # Always finish after memory update
    
    def _route_after_error(self, state: AgentState) -> Literal["triage", "planning", "research", "validation", "calculation", "placeholder", "synthesis", "finish"]:
        """Routes workflow after error handling."""
        if not state.get("error_state") or not state["error_state"].get("is_recoverable"):
            return "finish"
            
        # Retry the failed step
        failed_step = state["error_state"].get("failed_agent")
        if failed_step in ["triage", "planning", "research", "validation", "calculation", "placeholder", "synthesis"]:
            return failed_step
        return "finish" # Default to finish if failed step is unknown
    
    async def run(
        self, 
        user_query: str, 
        context_payload: str = "", 
        conversation_manager=None,
        thread_id: str = None
    ) -> Dict[str, Any]:
        """
        Runs the complete agentic workflow.
        
        Args:
            user_query: The user's input question
            context_payload: Context from conversation manager
            conversation_manager: ConversationManager instance
            thread_id: Optional thread ID for conversation tracking
            
        Returns:
            Complete workflow execution results
        """
        # Store conversation manager separately (not serializable in state)
        self.conversation_manager = conversation_manager
        
        # Inject conversation manager into memory agent
        if hasattr(self, 'memory_agent'):
            self.memory_agent._workflow_conversation_manager = conversation_manager
        
        # Create initial state
        initial_state = create_initial_state(
            user_query=user_query,
            context_payload=context_payload,
            conversation_manager=None,  # Don't pass to state (not serializable)
            debug_mode=self.debug_mode
        )
        
        self.logger.info(f"Starting workflow execution for query: {user_query[:100]}...")
        
        try:
            # Configure thread for conversation persistence
            config = {"configurable": {"thread_id": thread_id or f"thread_{datetime.now().isoformat()}"}}
            
            # Execute the workflow
            final_state = await self.app.ainvoke(initial_state, config=config)
            
            # Extract the final response
            final_response = self._extract_final_response(final_state)
            
            # Log completion
            response_preview = final_response[:100] if final_response else "No response"
            self.logger.info(f"Workflow completed successfully: {response_preview}...")
            
            # Return comprehensive results
            return {
                "response": final_response,
                "workflow_state": final_state,
                "execution_summary": self._create_execution_summary(final_state),
                "success": True
            }
            
        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}", exc_info=True)
            return {
                "response": f"I apologize, but I encountered an error processing your request: {str(e)}",
                "workflow_state": None,
                "execution_summary": {"error": str(e)},
                "success": False
            }
    
    def _extract_final_response(self, final_state: AgentState) -> str:
        """
        Extracts the final response from the workflow state.
        
        Args:
            final_state: Final workflow state
            
        Returns:
            Final response string
        """
        # Priority order for response extraction
        response = (
            final_state.get("final_answer") or
            final_state.get("direct_answer") or
            "I was unable to generate a response to your query."
        )
        
        return response
    
    def _create_execution_summary(self, final_state: AgentState) -> Dict[str, Any]:
        """
        Creates a summary of the workflow execution.
        
        Args:
            final_state: Final workflow state
            
        Returns:
            Execution summary dictionary
        """
        execution_log = final_state.get("execution_log", [])
        
        summary = {
            "total_execution_time_ms": final_state.get("total_execution_time_ms", 0.0),
            "agents_executed": len(execution_log),
            "workflow_path": [log.get("agent_name") for log in execution_log],
            "final_step": final_state.get("current_step"),
            "workflow_status": final_state.get("workflow_status"),
            "confidence_score": final_state.get("confidence_score", 0.0),
            "quality_metrics": final_state.get("quality_metrics", {}),
            "error_encountered": final_state.get("error_state") is not None,
            "retry_count": final_state.get("retry_count", 0)
        }
        
        # Add agent-specific summaries if available
        if final_state.get("intermediate_outputs"):
            summary["agent_details"] = final_state["intermediate_outputs"]
        
        return summary
    
    def get_workflow_visualization(self) -> str:
        """
        Returns a text representation of the workflow graph.
        
        Returns:
            Workflow visualization string
        """
        return """
LangGraph Agentic AI Workflow (Enhanced with Validation & Calculation):

┌─────────────┐
│   TRIAGE    │ ──── Classify query type and complexity
└─────────────┘
       │
       ▼
┌─────────────┐
│  PLANNING   │ ──── Generate research plan or direct answer
└─────────────┘
       │
       ▼
┌─────────────┐
│  RESEARCH   │ ──── Execute parallel research with fallbacks
└─────────────┘
       │
       ▼
┌─────────────┐
│ VALIDATION  │ ──── Validate research sufficiency & detect math needs
└─────────────┘
       │
       ├─── Insufficient ───┐
       │                    ▼
       │              ┌─────────────┐
       │              │ PLACEHOLDER │ ──── Handle insufficient research
       │              └─────────────┘
       │                    │
       ├─── Math Needed ────┤
       │                    ▼
       │              ┌─────────────┐
       │              │CALCULATION  │ ──── Execute Docker-based math
       │              └─────────────┘
       │                    │
       ▼                    ▼
┌─────────────┐◄────────────┘
│ SYNTHESIS   │ ──── Combine results into final answer
└─────────────┘
       │
       ▼
┌─────────────┐
│   MEMORY    │ ──── Update conversation and memory
└─────────────┘
       │
       ▼
┌─────────────┐
│   FINISH    │ ──── Return final response
└─────────────┘

Features:
- Research validation with sufficiency scoring
- Intelligent calculation detection (math library only)
- Docker-based secure code execution with retry
- Placeholder handling for incomplete research
- Error handling and retry logic at every step
"""

# Factory function for easy workflow creation
def create_agentic_workflow(debug: bool = False) -> AgenticWorkflow:
    """
    Factory function to create a configured agentic workflow.
    
    Args:
        debug: Whether to enable debug mode
        
    Returns:
        Configured AgenticWorkflow instance
    """
    return AgenticWorkflow(debug_mode=debug)

# Async wrapper for simple execution
async def run_agentic_query(
    user_query: str, 
    context_payload: str = "", 
    conversation_manager=None,
    debug: bool = False
) -> str:
    """
    Simple async wrapper for running a single query through the workflow.
    
    Args:
        user_query: The user's question
        context_payload: Context from conversation manager
        conversation_manager: ConversationManager instance
        debug: Whether to enable debug mode
        
    Returns:
        Final response string
    """
    workflow = create_agentic_workflow(debug=debug)
    result = await workflow.run(user_query, context_payload, conversation_manager)
    return result["response"] 