"""
Thinking-Enhanced LangGraph Workflow

This module implements a thinking-enabled version of the agentic workflow
that provides detailed reasoning visibility for all agent decisions.
"""

import sys
import os
from typing import Dict, Any, Literal, Optional
import logging
from datetime import datetime
import hashlib
import json

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# LangGraph imports
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_google_genai import ChatGoogleGenerativeAI

# Local imports
from state import AgentState, create_initial_state
from agents import (
    TriageAgent, ContextualAnsweringAgent, PlanningAgent, HydeAgent,
    ResearchOrchestrator, EnhancedSynthesisAgent, MemoryAgent, ErrorHandler,
    RetrievalStrategyAgent
)
from thinking_agents import (
    ThinkingValidationAgent,
)
from thinking_logger import ThinkingLogger, ThinkingMode
from cognitive_flow_agent_wrapper import CognitiveFlowAgentWrapper
from cognitive_flow import CognitiveFlowLogger

class ThinkingAgenticWorkflow:
    """
    Thinking-Enhanced LangGraph workflow with detailed reasoning visibility.
    """
    
    def __init__(self, debug_mode: bool = True, thinking_mode: bool = True, thinking_detail_mode: ThinkingMode = ThinkingMode.SIMPLE, cognitive_flow_logger: Optional[CognitiveFlowLogger] = None):
        self.debug_mode = debug_mode
        self.thinking_mode = thinking_mode
        self.thinking_detail_mode = thinking_detail_mode
        self.logger = logging.getLogger("ThinkingAgenticWorkflow")
        self.cognitive_flow_logger = cognitive_flow_logger
        self.llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest", temperature=0)

        self.workflow = self._build_workflow_graph()
        self.app = self._compile_workflow()
        self.logger.info(f"Thinking-enhanced workflow initialized (debug={debug_mode}, thinking={thinking_mode})")
    
    def _build_workflow_graph(self) -> StateGraph:
        """Build the workflow graph with our new agent architecture."""

        workflow = StateGraph(AgentState)
        
        # Add all agent nodes
        workflow.add_node("triage", CognitiveFlowAgentWrapper(TriageAgent(), self.cognitive_flow_logger))
        workflow.add_node("contextual_answering", CognitiveFlowAgentWrapper(ContextualAnsweringAgent(), self.cognitive_flow_logger))
        workflow.add_node("planning", CognitiveFlowAgentWrapper(PlanningAgent(), self.cognitive_flow_logger))
        workflow.add_node("hyde_generation", CognitiveFlowAgentWrapper(HydeAgent(), self.cognitive_flow_logger))
        workflow.add_node("research", CognitiveFlowAgentWrapper(ResearchOrchestrator(self.llm), self.cognitive_flow_logger))
        workflow.add_node("synthesis", CognitiveFlowAgentWrapper(EnhancedSynthesisAgent(), self.cognitive_flow_logger))
        workflow.add_node("memory_update", CognitiveFlowAgentWrapper(MemoryAgent(), self.cognitive_flow_logger))
        workflow.add_node("error_handler", CognitiveFlowAgentWrapper(ErrorHandler(), self.cognitive_flow_logger))
        
        workflow.set_entry_point("triage")
        
        workflow.add_conditional_edges(
            "triage",
            self._route_after_triage,
            {
                "planning": "planning",
                "research": "research",
                "contextual_answering": "contextual_answering",
                "finish": END,
                "error": "error_handler"
            }
        )
        
        workflow.add_conditional_edges(
            "contextual_answering",
            self._route_after_contextual_answering,
            {
                "planning": "planning",
                "finish": END,
                "error": "error_handler"
            }
        )
        
        workflow.add_edge("planning", "hyde_generation")
        workflow.add_edge("hyde_generation", "research")
        workflow.add_edge("research", "synthesis")
        workflow.add_edge("synthesis", "memory_update")
        workflow.add_edge("memory_update", END)
        workflow.add_edge("error_handler", END)
        
        return workflow
    
    def _compile_workflow(self):
        """Compile the workflow with memory management."""
        memory = MemorySaver()
        return self.workflow.compile(checkpointer=memory)
    
    def _route_after_triage(self, state: AgentState) -> Literal["planning", "contextual_answering", "finish", "error"]:
        """Route after triage based on the new, sophisticated classification."""
        if state.get("error_state"):
            return "error"
        classification = state.get("triage_classification")
        if classification == "simple_response": 
            return "finish"
        if classification == "contextual_clarification": 
            return "contextual_answering"
        if classification == "direct_retrieval": 
            return "research"
        return "planning"

    def _route_after_contextual_answering(self, state: AgentState) -> Literal["finish", "planning", "error"]:
        """Routes after the contextual answering agent attempts a response."""
        if state.get("error_state"):
            return "error"
        return "finish" if state.get("contextual_answer_success") else "planning"
    
    async def run(self, user_query: str, context_payload: str = "", conversation_manager=None, thread_id: str = None) -> Dict[str, Any]:
        initial_state = create_initial_state(user_query, context_payload, conversation_manager, thread_id)
        # The thread_id must be passed in the 'configurable' dictionary for the checkpointer.
        config = {"configurable": {"thread_id": thread_id}}
        final_state = await self.app.ainvoke(initial_state, config=config)
        summary = self._create_execution_summary(final_state)
        self.logger.info(f"Execution summary: {summary}")
        final_state["response"] = self._extract_final_response(final_state)
        return final_state
    
    def _extract_final_response(self, final_state: AgentState) -> str:
        """Extracts the final response from the agent state."""
        return final_state.get("final_answer", "No answer could be generated.")
    
    def _create_execution_summary(self, final_state: AgentState) -> Dict[str, Any]:
        """Creates a summary of the execution from the final state."""
        research_plan = final_state.get("research_plan", [])
        if research_plan is None:
            research_plan = []
        
        return {
            "triage_classification": final_state.get("triage_classification"),
            "research_queries": [task.get("sub_query") for task in research_plan],
            "final_answer_length": len(final_state.get("final_answer", "")),
            "error": final_state.get("error_state"),
        }

def create_thinking_agentic_workflow(debug=True, *args, **kwargs) -> ThinkingAgenticWorkflow:
    """Factory function to create the agentic workflow."""
    return ThinkingAgenticWorkflow(debug_mode=debug, *args, **kwargs)