"""
Thinking-Enhanced LangGraph Workflow

This module implements a thinking-enabled version of the agentic workflow
that provides detailed reasoning visibility for all agent decisions.
"""

import sys
import os
from typing import Dict, Any, List, Literal
import logging
from datetime import datetime
import hashlib
import json

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# LangGraph imports
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# Local imports
from state import AgentState, create_initial_state, is_workflow_complete, should_retry
from agents import (
    TriageAgent, PlanningAgent, ResearchOrchestrator, 
    SynthesisAgent, MemoryAgent, ErrorHandler
)

# Thinking agents imports
from thinking_agents import (
    ThinkingValidationAgent,
    ThinkingCalculationExecutor,
    ThinkingPlaceholderHandler
)

from thinking_logger import ThinkingLogger, ThinkingMode
from config import redis_client

class ThinkingAgenticWorkflow:
    """
    Thinking-Enhanced LangGraph workflow with detailed reasoning visibility.
    
    This workflow provides complete transparency into agent decision-making
    processes while maintaining all the advanced features of the original system.
    """
    
    def __init__(self, debug_mode: bool = True, thinking_mode: bool = True, thinking_detail_mode: ThinkingMode = ThinkingMode.SIMPLE):
        """
        Initialize the thinking-enhanced workflow.
        
        Args:
            debug_mode: Whether to enable debug logging
            thinking_mode: Whether to enable thinking process logging
            thinking_detail_mode: Simple or detailed thinking display mode
        """
        self.debug_mode = debug_mode
        self.thinking_mode = thinking_mode
        self.thinking_detail_mode = thinking_detail_mode
        self.logger = logging.getLogger("ThinkingAgenticWorkflow")
        self.conversation_manager = None
        
        # Initialize workflow thinking logger
        self.workflow_thinking = ThinkingLogger(
            agent_name="WorkflowOrchestrator",
            console_output=thinking_mode,
            detailed_logging=debug_mode,
            thinking_mode=thinking_detail_mode
        ) if thinking_mode else None
        
        # Initialize agents
        self._initialize_agents()
        
        # Build the workflow graph
        self.workflow = self._build_workflow_graph()
        
        # Compile the workflow
        self.app = self._compile_workflow()
        
        self.logger.info(f"Thinking-enhanced workflow initialized (debug={debug_mode}, thinking={thinking_mode})")
    
    def _initialize_agents(self):
        """Initialize all agents including thinking-enhanced versions."""
        
        if self.thinking_mode and self.workflow_thinking:
            with self.workflow_thinking.thinking_block("Agent Initialization"):
                self.workflow_thinking.craft("Initializing sophisticated agent ensemble...")
        
        # Import Enhanced agents (preserving original functionality)
        from agents.planning_agent import EnhancedPlanningAgent
        from agents.research_orchestrator import EnhancedResearchOrchestrator
        from agents.synthesis_agent import EnhancedSynthesisAgent
        from agents.memory_agent import EnhancedMemoryAgent
        
        # Initialize core agents
        self.triage_agent = TriageAgent()
        self.planning_agent = EnhancedPlanningAgent()
        self.research_agent = EnhancedResearchOrchestrator()
        self.synthesis_agent = EnhancedSynthesisAgent()
        self.memory_agent = EnhancedMemoryAgent()
        self.error_handler = ErrorHandler()
        
        # Initialize thinking-enhanced agents with proper thinking mode
        self.validation_agent = ThinkingValidationAgent(thinking_mode=self.thinking_detail_mode)
        self.calculation_executor = ThinkingCalculationExecutor(thinking_mode=self.thinking_detail_mode)
        self.placeholder_handler = ThinkingPlaceholderHandler(thinking_mode=self.thinking_detail_mode)
        
        if self.thinking_mode and self.workflow_thinking:
            self.workflow_thinking.success("✅ All agents initialized successfully")
            self.workflow_thinking.note("Enhanced agents: ValidationAgent, CalculationExecutor, PlaceholderHandler")
    
    def _build_workflow_graph(self) -> StateGraph:
        """Build the workflow graph with thinking-enhanced agents."""
        
        if self.thinking_mode and self.workflow_thinking:
            with self.workflow_thinking.thinking_block("Workflow Graph Construction"):
                self.workflow_thinking.craft("Building sophisticated agent orchestration graph...")
        
        # Create the state graph
        workflow = StateGraph(AgentState)
        
        # Add all agent nodes
        workflow.add_node("triage", self.triage_agent)
        workflow.add_node("planning", self.planning_agent)
        workflow.add_node("research", self.research_agent)
        
        # Add thinking-enhanced nodes
        workflow.add_node("validation", self.validation_agent)
        workflow.add_node("calculation", self.calculation_executor)
        workflow.add_node("placeholder", self.placeholder_handler)
        
        workflow.add_node("synthesis", self.synthesis_agent)
        workflow.add_node("memory_update", self.memory_agent)
        workflow.add_node("error_handler", self.error_handler)
        
        # Set entry point
        workflow.set_entry_point("triage")
        
        # Add conditional edges with thinking-aware routing
        workflow.add_conditional_edges(
            "triage",
            self._route_after_triage_with_thinking,
            {
                "planning": "planning",
                "finish": END,
                "error": "error_handler"
            }
        )
        
        workflow.add_conditional_edges(
            "planning",
            self._route_after_planning_with_thinking,
            {
                "research": "research",
                "finish": END,
                "error": "error_handler"
            }
        )
        
        workflow.add_conditional_edges(
            "research",
            self._route_after_research_with_thinking,
            {
                "validation": "validation",
                "error": "error_handler"
            }
        )
        
        # Enhanced routing for thinking agents
        workflow.add_conditional_edges(
            "validation",
            self._route_after_validation_with_thinking,
            {
                "calculation": "calculation",
                "placeholder": "placeholder", 
                "synthesis": "synthesis",
                "error": "error_handler"
            }
        )
        
        workflow.add_conditional_edges(
            "calculation",
            self._route_after_calculation_with_thinking,
            {
                "synthesis": "synthesis",
                "error": "error_handler"
            }
        )
        
        workflow.add_conditional_edges(
            "placeholder",
            self._route_after_placeholder_with_thinking,
            {
                "synthesis": "synthesis",
                "error": "error_handler"
            }
        )
        
        workflow.add_conditional_edges(
            "synthesis",
            self._route_after_synthesis_with_thinking,
            {
                "memory_update": "memory_update",
                "error": "error_handler"
            }
        )
        
        workflow.add_conditional_edges(
            "memory_update",
            self._route_after_memory_with_thinking,
            {
                "finish": END,
                "error": "error_handler"
            }
        )
        
        workflow.add_conditional_edges(
            "error_handler",
            self._route_after_error_with_thinking,
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
        
        if self.thinking_mode and self.workflow_thinking:
            self.workflow_thinking.success("✅ Workflow graph constructed with 9 agents and intelligent routing")
        
        return workflow
    
    def _compile_workflow(self):
        """Compile the workflow with memory management."""
        memory = MemorySaver()
        return self.workflow.compile(checkpointer=memory)
    
    # Thinking-enhanced routing methods
    def _route_after_triage_with_thinking(self, state: AgentState) -> Literal["planning", "finish", "error"]:
        """Route after triage with thinking process."""
        
        if self.thinking_mode and self.workflow_thinking:
            with self.workflow_thinking.decision_tree("Post-Triage Routing"):
                triage_classification = state.get("triage_classification")
                self.workflow_thinking.weigh(f"Triage classification: {triage_classification}")
                
                if state.get("error_state"):
                    self.workflow_thinking.problem("Error state detected")
                    self.workflow_thinking.decide("Route to error handler")
                    return "error"
                elif triage_classification == "engage":
                    self.workflow_thinking.reason("Query requires full processing")
                    self.workflow_thinking.decide("Proceed to planning")
                    return "planning"
                elif triage_classification == "direct_retrieval":
                    self.workflow_thinking.reason("Direct retrieval identified, routing to planning agent for execution.")
                    self.workflow_thinking.decide("Proceed to planning")
                    return "planning"
                else:
                    self.workflow_thinking.reason("Query can be handled directly by the Triage agent's response.")
                    self.workflow_thinking.decide("Skip to finish")
                    return "finish"
        
        # Original routing logic
        if state.get("error_state"):
            return "error"
        
        triage_classification = state.get("triage_classification")
        if triage_classification == "engage" or triage_classification == "direct_retrieval":
            return "planning"
        else:
            return "finish"
    
    def _route_after_planning_with_thinking(self, state: AgentState) -> Literal["research", "finish", "error"]:
        """Route after planning with thinking process."""
        
        if self.thinking_mode and self.workflow_thinking:
            with self.workflow_thinking.decision_tree("Post-Planning Routing"):
                planning_classification = state.get("planning_classification")
                self.workflow_thinking.weigh(f"Planning classification: {planning_classification}")
                
                if state.get("error_state"):
                    self.workflow_thinking.problem("Error state detected")
                    self.workflow_thinking.decide("Route to error handler")
                    return "error"
                elif planning_classification in ["simple_answer", "direct_retrieval"]:
                    self.workflow_thinking.reason("Direct answer provided by planning")
                    self.workflow_thinking.decide("Skip to finish")
                    return "finish"
                elif planning_classification == "engage":
                    self.workflow_thinking.reason("Comprehensive research required")
                    self.workflow_thinking.decide("Proceed to research")
                    return "research"
                else:
                    self.workflow_thinking.reason("Default case - proceeding to finish")
                    self.workflow_thinking.decide("Route to finish")
                    return "finish"
        
        # Original routing logic
        if state.get("error_state"):
            return "error"
        
        planning_classification = state.get("planning_classification")
        if planning_classification in ["simple_answer", "direct_retrieval"]:
            return "finish"
        elif planning_classification == "engage":
            return "research"
        else:
            return "finish"
    
    def _route_after_research_with_thinking(self, state: AgentState) -> Literal["validation", "error"]:
        """Route after research with thinking process."""
        
        if self.thinking_mode and self.workflow_thinking:
            with self.workflow_thinking.decision_tree("Post-Research Routing"):
                research_results = state.get("sub_query_answers", [])
                self.workflow_thinking.analyze(f"Research completed with {len(research_results)} results")
                
                if state.get("error_state"):
                    self.workflow_thinking.problem("Error state detected in research")
                    self.workflow_thinking.decide("Route to error handler")
                    return "error"
                else:
                    self.workflow_thinking.reason("Research complete - needs validation and math detection")
                    self.workflow_thinking.decide("Proceed to validation agent")
                    return "validation"
        
        if state.get("error_state"):
            return "error"
        return "validation"
    
    def _route_after_validation_with_thinking(self, state: AgentState) -> Literal["calculation", "placeholder", "synthesis", "error"]:
        """Route after validation with thinking process."""
        
        if self.thinking_mode and self.workflow_thinking:
            with self.workflow_thinking.decision_tree("Post-Validation Routing"):
                if state.get("error_state"):
                    self.workflow_thinking.problem("Error state detected in validation")
                    self.workflow_thinking.decide("Route to error handler")
                    return "error"
                
                # Get validation results
                validation_results = state.get("research_validation_results", {})
                research_sufficient = validation_results.get("is_sufficient", False)
                math_calculation_needed = state.get("math_calculation_needed", False)
                math_types = state.get("math_calculation_types", [])
                
                self.workflow_thinking.weigh(f"Research sufficient: {research_sufficient}")
                self.workflow_thinking.weigh(f"Math calculation needed: {math_calculation_needed}")
                self.workflow_thinking.weigh(f"Math types: {math_types}")
                
                # ABSOLUTE PRIORITY: Math calculations ALWAYS go to CalculationExecutor
                if math_calculation_needed:
                    self.workflow_thinking.reason("🔢 MATH DETECTED - Absolute priority for calculation execution")
                    self.workflow_thinking.decide("Route to CalculationExecutor (OVERRIDES research sufficiency)")
                    return "calculation"
                
                # Only use PlaceholderHandler when NO math is needed AND research is insufficient
                if not research_sufficient:
                    self.workflow_thinking.reason("📝 No math needed, but research gaps identified")
                    self.workflow_thinking.decide("Route to PlaceholderHandler for research gaps")
                    return "placeholder"
                else:
                    self.workflow_thinking.reason("✅ Research sufficient, no calculations needed")
                    self.workflow_thinking.decide("Route directly to Synthesis")
                    return "synthesis"
        
        if state.get("error_state"):
            return "error"
        
        # Non-thinking mode fallback with same fixed logic
        validation_results = state.get("research_validation_results", {})
        research_sufficient = validation_results.get("is_sufficient", False)
        math_calculation_needed = state.get("math_calculation_needed", False)
        
        # ABSOLUTE PRIORITY: Math calculations ALWAYS go to CalculationExecutor
        if math_calculation_needed:
            return "calculation"
        
        # Only use PlaceholderHandler when NO math is needed AND research is insufficient
        if not research_sufficient:
            return "placeholder"
        else:
            return "synthesis"
    
    def _route_after_calculation_with_thinking(self, state: AgentState) -> Literal["synthesis", "error"]:
        """Route after calculation with thinking process."""
        
        if self.thinking_mode and self.workflow_thinking:
            with self.workflow_thinking.decision_tree("Post-Calculation Routing"):
                calc_success = state.get("calculation_execution_success", False)
                self.workflow_thinking.analyze(f"Calculation execution success: {calc_success}")
                
                if state.get("error_state"):
                    self.workflow_thinking.problem("Error state detected in calculation")
                    self.workflow_thinking.decide("Route to error handler")
                    return "error"
                else:
                    self.workflow_thinking.reason("Calculation phase complete (success or graceful failure)")
                    self.workflow_thinking.decide("Proceed to synthesis with enhanced context")
                    return "synthesis"
        
        if state.get("error_state"):
            return "error"
        return "synthesis"
    
    def _route_after_placeholder_with_thinking(self, state: AgentState) -> Literal["synthesis", "error"]:
        """Route after placeholder with thinking process."""
        
        if self.thinking_mode and self.workflow_thinking:
            with self.workflow_thinking.decision_tree("Post-Placeholder Routing"):
                placeholder_count = state.get("synthesis_metadata", {}).get("placeholder_count", 0)
                self.workflow_thinking.analyze(f"Placeholder handling complete with {placeholder_count} placeholders")
                
                if state.get("error_state"):
                    self.workflow_thinking.problem("Error state detected in placeholder handling")
                    self.workflow_thinking.decide("Route to error handler")
                    return "error"
                else:
                    self.workflow_thinking.reason("Placeholder content prepared for synthesis")
                    self.workflow_thinking.decide("Proceed to synthesis with partial answer")
                    return "synthesis"
        
        if state.get("error_state"):
            return "error"
        return "synthesis"
    
    def _route_after_synthesis_with_thinking(self, state: AgentState) -> Literal["memory_update", "error"]:
        """Route after synthesis with thinking process."""
        
        if self.thinking_mode and self.workflow_thinking:
            with self.workflow_thinking.decision_tree("Post-Synthesis Routing"):
                final_answer = state.get("final_answer")
                self.workflow_thinking.analyze(f"Synthesis complete with answer length: {len(final_answer) if final_answer else 0}")
                
                if state.get("error_state"):
                    self.workflow_thinking.problem("Error state detected in synthesis")
                    self.workflow_thinking.decide("Route to error handler")
                    return "error"
                else:
                    self.workflow_thinking.reason("Final answer synthesized successfully")
                    self.workflow_thinking.decide("Proceed to memory update")
                    return "memory_update"
        
        if state.get("error_state"):
            return "error"
        return "memory_update"
    
    def _route_after_memory_with_thinking(self, state: AgentState) -> Literal["finish", "error"]:
        """Route after memory with thinking process."""
        
        if self.thinking_mode and self.workflow_thinking:
            with self.workflow_thinking.decision_tree("Post-Memory Routing"):
                memory_updated = state.get("memory_update_completed", False)
                self.workflow_thinking.analyze(f"Memory update completed: {memory_updated}")
                
                if state.get("error_state"):
                    self.workflow_thinking.problem("Error state detected in memory update")
                    self.workflow_thinking.decide("Route to error handler")
                    return "error"
                else:
                    self.workflow_thinking.reason("Memory successfully updated")
                    self.workflow_thinking.decide("Workflow complete - finishing")
                    return "finish"
        
        if state.get("error_state"):
            return "error"
        return "finish"
    
    def _route_after_error_with_thinking(self, state: AgentState) -> Literal["triage", "planning", "research", "validation", "calculation", "placeholder", "synthesis", "finish"]:
        """Route after error with thinking process."""
        
        if self.thinking_mode and self.workflow_thinking:
            with self.workflow_thinking.decision_tree("Post-Error Recovery Routing"):
                recovery_action = state.get("recovery_action")
                retry_step = state.get("retry_step")
                retry_count = state.get("retry_count", 0)
                
                self.workflow_thinking.analyze(f"Error recovery: action={recovery_action}, retry_step={retry_step}, count={retry_count}")
                
                if recovery_action == "retry" and retry_step:
                    self.workflow_thinking.reason(f"Retrying from step: {retry_step}")
                    self.workflow_thinking.decide(f"Route to {retry_step}")
                    return retry_step
                elif recovery_action in ["planning_fallback"]:
                    self.workflow_thinking.reason("Using planning fallback strategy")
                    self.workflow_thinking.decide("Route to research")
                    return "research"
                elif recovery_action in ["research_fallback"]:
                    self.workflow_thinking.reason("Using research fallback strategy")
                    self.workflow_thinking.decide("Route to validation")
                    return "validation"
                else:
                    self.workflow_thinking.reason("No recovery possible or graceful degradation")
                    self.workflow_thinking.decide("Finish with error state")
                    return "finish"
        
        recovery_action = state.get("recovery_action")
        retry_step = state.get("retry_step")
        
        if recovery_action == "retry" and retry_step:
            return retry_step
        elif recovery_action in ["planning_fallback"]:
            return "research"
        elif recovery_action in ["research_fallback"]:
            return "validation"
        else:
            return "finish"
    
    async def run(self, user_query: str, context_payload: str = "", conversation_manager=None, thread_id: str = None) -> Dict[str, Any]:
        """
        Executes the thinking-enhanced agentic workflow for a given query.
        """
        if self.thinking_mode and self.workflow_thinking:
            with self.workflow_thinking.thinking_block(f"Executing query: '{user_query}'"):
                self.workflow_thinking.craft("Starting thinking-enhanced workflow...")
        
        # Store conversation manager
        self.conversation_manager = conversation_manager
        
        # Inject conversation manager into memory agent
        if hasattr(self, 'memory_agent'):
            self.memory_agent._workflow_conversation_manager = conversation_manager
        
        # Create initial state
        initial_state = create_initial_state(
            user_query=user_query,
            context_payload=context_payload,
            conversation_manager=None,
            debug_mode=self.debug_mode
        )
        
        if self.thinking_mode and self.workflow_thinking:
            self.workflow_thinking.review("Initial state created successfully")
        
        try:
            # Configure thread for conversation persistence
            config = {"configurable": {"thread_id": thread_id or f"thread_{datetime.now().isoformat()}"}}
            
            if self.thinking_mode and self.workflow_thinking:
                self.workflow_thinking.attempt("Executing workflow through LangGraph orchestration...")
            
            # Execute the workflow
            final_state = await self.app.ainvoke(initial_state, config=config)
            
            # Extract the final response
            final_response = self._extract_final_response(final_state)
            
            # This is the full result object we will cache
            result_to_cache = {
                "response": final_response,
                "workflow_state": final_state,
                "execution_summary": self._create_execution_summary(final_state),
                "success": True
            }

            if self.thinking_mode and self.workflow_thinking:
                self.workflow_thinking.success("✅ Workflow completed successfully.")
            
            return result_to_cache
            
        except Exception as e:
            if self.thinking_mode and self.workflow_thinking:
                self.workflow_thinking.problem(f"Workflow execution failed: {str(e)}")
                self.workflow_thinking.end_session()
            
            self.logger.error(f"Thinking workflow execution failed: {e}", exc_info=True)
            return {
                "response": f"I apologize, but I encountered an error processing your request: {str(e)}",
                "workflow_state": None,
                "execution_summary": {"error": str(e)},
                "success": False
            }
    
    def _extract_final_response(self, final_state: AgentState) -> str:
        """Extract the final response from the workflow state."""
        response = (
            final_state.get("final_answer") or
            final_state.get("direct_answer") or
            "I was unable to generate a response to your query."
        )
        return response
    
    def _create_execution_summary(self, final_state: AgentState) -> Dict[str, Any]:
        """Create a comprehensive execution summary."""
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
            "retry_count": final_state.get("retry_count", 0),
            
            # Enhanced metrics for thinking workflow
            "research_sufficient": final_state.get("research_sufficient", False),
            "math_calculation_needed": final_state.get("math_calculation_needed", False),
            "calculation_success": final_state.get("calculation_execution_success", False),
            "enhancement_triggered": final_state.get("enhancement_pipeline_triggered", False)
        }
        
        return summary
    
    def get_workflow_visualization(self) -> str:
        """Get workflow visualization with thinking enhancements."""
        
        visualization = """
        🧠 THINKING-ENHANCED AGENTIC WORKFLOW
        =====================================
        
        📥 INPUT
         ↓
        🎯 TRIAGE ──→ [analyze query type & complexity]
         ↓
        📋 PLANNING ──→ [create research strategy]
         ↓
        🔍 RESEARCH ──→ [parallel information gathering]
         ↓
        ✅ VALIDATION ──→ [🧠 THINKING: research sufficiency + math detection]
         ├─ Insufficient Research ──→ 📝 PLACEHOLDER ──→ [🧠 THINKING: gap analysis]
         ├─ Math Needed ──→ 🧮 CALCULATION ──→ [🧠 THINKING: code generation + retry]
         └─ Ready ──→ 📖 SYNTHESIS
         ↓
        🧠 MEMORY UPDATE
         ↓
        📤 OUTPUT
        
        🧠 THINKING CAPABILITIES:
        - ValidationAgent: Research quality analysis & calculation detection
        - CalculationExecutor: Code generation with intelligent retry
        - PlaceholderHandler: Professional gap management
        - WorkflowOrchestrator: Decision transparency at each routing point
        """
        
        return visualization

# Factory functions for easy usage
def create_thinking_agentic_workflow(debug: bool = True, thinking_mode: bool = True, thinking_detail_mode: ThinkingMode = ThinkingMode.SIMPLE) -> ThinkingAgenticWorkflow:
    """Create a thinking-enhanced agentic workflow."""
    return ThinkingAgenticWorkflow(debug_mode=debug, thinking_mode=thinking_mode, thinking_detail_mode=thinking_detail_mode)

async def run_thinking_agentic_query(
    user_query: str, 
    context_payload: str = "", 
    conversation_manager=None,
    debug: bool = True,
    thinking_mode: bool = True
) -> str:
    """Run a query through the thinking-enhanced agentic workflow."""
    workflow = create_thinking_agentic_workflow(debug=debug, thinking_mode=thinking_mode)
    result = await workflow.run(
        user_query=user_query,
        context_payload=context_payload,
        conversation_manager=conversation_manager
    )
    return result["response"] 