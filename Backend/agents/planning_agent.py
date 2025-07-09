"""
Planning Agent for LangGraph workflow.

This agent integrates the sophisticated planning logic from the original
PlanningTool, handling query decomposition, HyDE generation, and direct retrieval.
It preserves all the advanced logic while adapting to the LangGraph state system.
"""

import json
import re
from typing import Dict, Any, List

# Add parent directories to path for imports
from .base_agent import BaseLangGraphAgent
from state import AgentState
from state_keys import (
    USER_QUERY, CONTEXT_PAYLOAD, CURRENT_STEP, WORKFLOW_STATUS,
    TRIAGE_CLASSIFICATION, PLANNING_CLASSIFICATION, PLANNING_REASONING,
    RESEARCH_PLAN, DIRECT_ANSWER
)

# Import the original planning tool logic
from tools.planning_tool import PlanningTool
from tools.neo4j_connector import Neo4jConnector

class PlanningAgent(BaseLangGraphAgent):
    """
    Planning Agent for sophisticated query analysis and research planning.
    
    This agent leverages the existing PlanningTool implementation while
    adapting it to the LangGraph workflow. It handles:
    - Query classification and validation
    - Direct retrieval for specific entities
    - Research plan generation with HyDE documents
    - Query decomposition for complex questions
    """
    
    def __init__(self):
        """Initialize the Planning Agent with Tier 1 model for sophisticated planning."""
        super().__init__(model_tier="tier_1", agent_name="PlanningAgent")
        
        # Initialize the original planning tool
        self.planning_tool = PlanningTool()
        
        # Ensure Neo4j connector is available
        try:
            Neo4jConnector.get_driver()
            self.logger.info("Neo4j connector initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Neo4j connector: {e}")
            raise
    
    async def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute the planning logic using the original PlanningTool.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dictionary containing planning results
        """
        user_query = state[USER_QUERY]
        context_payload = state.get(CONTEXT_PAYLOAD, "")
        
        # Use triage classification if available, otherwise use planning classification
        classification = state.get(TRIAGE_CLASSIFICATION) or state.get(PLANNING_CLASSIFICATION)
        
        self.logger.info(f"Planning for query: {user_query[:100]}...")
        self.logger.info(f"Input classification: {classification}")
        
        try:
            # Call the original planning tool
            planning_result = self.planning_tool(
                query=user_query,
                context_payload=context_payload
            )
            
            self.logger.info(f"Planning tool result: {planning_result.get('classification', 'unknown')}")
            
            # Process the planning result based on classification
            return await self._process_planning_result(planning_result, state)
            
        except Exception as e:
            self.logger.error(f"Error in planning tool execution: {e}")
            # Fallback to basic engage classification
            return {
                PLANNING_CLASSIFICATION: "engage",
                PLANNING_REASONING: f"Planning tool error: {str(e)}, falling back to engage",
                RESEARCH_PLAN: [{
                    "sub_query": user_query,
                    "hyde_document": f"Fallback research for: {user_query}"
                }],
                CURRENT_STEP: "research",
                WORKFLOW_STATUS: "running"
            }
    
    async def _process_planning_result(self, planning_result: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """
        Processes the result from the planning tool and formats it for LangGraph state.
        
        Args:
            planning_result: Result from the original planning tool
            state: Current workflow state
            
        Returns:
            Formatted planning output for state update
        """
        classification = planning_result.get("classification")
        
        if classification == "simple_answer":
            # Direct answer provided by planning tool
            return {
                PLANNING_CLASSIFICATION: "simple_answer",
                PLANNING_REASONING: "Planning tool provided a direct answer",
                DIRECT_ANSWER: planning_result.get("direct_answer", "Direct answer provided."),
                CURRENT_STEP: "finish",
                WORKFLOW_STATUS: "completed"
            }
        
        elif classification == "engage":
            # Complex query requiring research
            plan = planning_result.get("plan", [])
            
            if not plan:
                self.logger.warning("Engage classification but no plan provided, creating fallback")
                plan = [{
                    "sub_query": state[USER_QUERY],
                    "hyde_document": f"Research the following question from the Virginia Building Code: {state[USER_QUERY]}"
                }]
            
            return {
                PLANNING_CLASSIFICATION: "engage",
                PLANNING_REASONING: planning_result.get("reasoning", "Complex query requiring research"),
                RESEARCH_PLAN: plan,
                CURRENT_STEP: "research",
                WORKFLOW_STATUS: "running"
            }
        
        elif classification == "direct_retrieval":
            # Direct entity lookup - pass context to synthesis
            return {
                PLANNING_CLASSIFICATION: "direct_retrieval", 
                PLANNING_REASONING: planning_result.get("reasoning", "Direct entity retrieval"),
                "retrieved_context": planning_result.get("retrieved_context"),
                "retrieved_diagrams": planning_result.get("retrieved_diagrams"),
                CURRENT_STEP: "synthesis"
            }
        
        else:
            # Unknown classification, default to engage
            self.logger.warning(f"Unknown classification '{classification}', defaulting to engage")
            return {
                PLANNING_CLASSIFICATION: "engage",
                PLANNING_REASONING: f"Unknown classification '{classification}', defaulting to research",
                RESEARCH_PLAN: [{
                    "sub_query": state[USER_QUERY],
                    "hyde_document": f"Research the following question: {state[USER_QUERY]}"
                }],
                CURRENT_STEP: "research", 
                WORKFLOW_STATUS: "running"
            }
    
    def _validate_agent_specific_state(self, state: AgentState) -> None:
        """
        Validates planning agent specific state requirements.
        
        Args:
            state: State to validate
            
        Raises:
            ValueError: If required fields are missing
        """
        if not state.get(USER_QUERY):
            raise ValueError("user_query is required for planning")
        
        # Check that we're in the right step
        if state.get(CURRENT_STEP) not in ["planning", "triage"]:
            self.logger.warning(f"Unexpected current_step '{state.get(CURRENT_STEP)}' for planning agent")
    
    def _apply_agent_specific_updates(self, state: AgentState, output_data: Dict[str, Any]) -> AgentState:
        """
        Applies planning-specific state updates.
        
        Args:
            state: Current state
            output_data: Planning output data
            
        Returns:
            Updated state
        """
        updated_state = state.copy()
        
        # Store planning metadata for debugging
        if updated_state.get("intermediate_outputs") is not None:
            updated_state["intermediate_outputs"]["planning_details"] = {
                "classification": output_data.get(PLANNING_CLASSIFICATION),
                "reasoning": output_data.get(PLANNING_REASONING),
                "plan_size": len(output_data.get(RESEARCH_PLAN, [])),
                "has_direct_answer": output_data.get(DIRECT_ANSWER) is not None
            }
        
        # Set quality metrics if we have a direct answer
        if output_data.get(DIRECT_ANSWER):
            updated_state["confidence_score"] = 0.85  # High confidence for direct answers
            if updated_state.get("quality_metrics") is not None:
                updated_state["quality_metrics"]["synthesis_quality_score"] = 0.85
        
        return updated_state

class EnhancedPlanningAgent(PlanningAgent):
    """
    Enhanced Planning Agent with additional LangGraph-specific optimizations.
    
    This version includes extra features for the LangGraph workflow while
    maintaining full compatibility with the original planning logic.
    """
    
    def __init__(self):
        """Initialize the Enhanced Planning Agent."""
        super().__init__()
        self.agent_name = "EnhancedPlanningAgent"
        
        # Additional planning strategies
        self.planning_strategies = {
            "code_calculation": self._handle_calculation_query,
            "code_comparison": self._handle_comparison_query,
            "requirement_lookup": self._handle_requirement_query,
            "compliance_check": self._handle_compliance_query
        }
    
    async def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        Enhanced execution with strategy-based planning.
        """
        # Fall back to original planning logic
        return await super().execute(state)

    async def _try_enhanced_strategies(self, state: AgentState) -> Dict[str, Any]:
        """
        Tries enhanced planning strategies for specific query types.
        """
        # This is where enhanced strategies would be tried first.
        # For now, we fall back to the base implementation.
        return None
    
    async def _handle_calculation_query(self, state: AgentState) -> Dict[str, Any]:
        """Handles calculation-specific queries with enhanced planning."""
        return {
            PLANNING_CLASSIFICATION: "engage",
            PLANNING_REASONING: "Calculation query detected - enhanced planning for formulas and variables",
            RESEARCH_PLAN: [
                {
                    "sub_query": f"What is the specific formula or equation for: {state[USER_QUERY]}",
                    "hyde_document": "The Virginia Building Code provides specific formulas and equations for structural calculations. The formula typically includes variables such as load factors, material properties, and geometric parameters."
                },
                {
                    "sub_query": f"What are the variable definitions and units for: {state[USER_QUERY]}",
                    "hyde_document": "Building code formulas require precise definition of variables including units, acceptable ranges, and calculation methods."
                }
            ],
            CURRENT_STEP: "research",
            WORKFLOW_STATUS: "running"
        }
    
    async def _handle_comparison_query(self, state: AgentState) -> Dict[str, Any]:
        """Handles comparison queries with enhanced planning."""
        return {
            PLANNING_CLASSIFICATION: "engage", 
            PLANNING_REASONING: "Comparison query detected - enhanced planning for multiple entities",
            RESEARCH_PLAN: [
                {
                    "sub_query": f"First component of comparison: {state[USER_QUERY]}",
                    "hyde_document": "Building code sections provide specific requirements, conditions, and applications for different structural elements and building types."
                },
                {
                    "sub_query": f"Second component of comparison: {state[USER_QUERY]}",
                    "hyde_document": "Comparative analysis requires understanding the specific requirements, limitations, and applications defined in the building code."
                }
            ],
            CURRENT_STEP: "research",
            WORKFLOW_STATUS: "running"
        }
    
    async def _handle_requirement_query(self, state: AgentState) -> Dict[str, Any]:
        """Handles requirement-specific queries."""
        return {
            PLANNING_CLASSIFICATION: "engage",
            PLANNING_REASONING: "Requirements query detected - enhanced planning for regulatory content",
            RESEARCH_PLAN: [
                {
                    "sub_query": f"Specific requirements for: {state[USER_QUERY]}",
                    "hyde_document": "The Virginia Building Code establishes specific requirements including minimum standards, conditions for application, and compliance criteria."
                }
            ],
            CURRENT_STEP: "research",
            WORKFLOW_STATUS: "running"
        }
    
    async def _handle_compliance_query(self, state: AgentState) -> Dict[str, Any]:
        """Handles compliance checking queries."""
        return {
            PLANNING_CLASSIFICATION: "engage",
            PLANNING_REASONING: "Compliance query detected - enhanced planning for code verification",
            RESEARCH_PLAN: [
                {
                    "sub_query": f"Compliance requirements and criteria for: {state[USER_QUERY]}",
                    "hyde_document": "Building code compliance requires meeting specific criteria, following prescribed methods, and satisfying regulatory requirements as outlined in the Virginia Building Code."
                }
            ],
            CURRENT_STEP: "research",
            WORKFLOW_STATUS: "running"
        }

    def _validate_agent_specific_state(self, state: AgentState) -> None:
        """
        Validates planning agent specific state requirements.
        
        Args:
            state: State to validate
            
        Raises:
            ValueError: If required fields are missing
        """
        if not state.get(USER_QUERY):
            raise ValueError("user_query is required for planning")
        
        # Check that we're in the right step
        if state.get(CURRENT_STEP) not in ["planning", "triage"]:
            self.logger.warning(f"Unexpected current_step '{state.get(CURRENT_STEP)}' for planning agent")
    
    def _apply_agent_specific_updates(self, state: AgentState, output_data: Dict[str, Any]) -> AgentState:
        """
        Applies planning-specific state updates.
        
        Args:
            state: Current state
            output_data: Planning output data
            
        Returns:
            Updated state
        """
        updated_state = state.copy()
        
        # Store planning metadata for debugging
        if updated_state.get("intermediate_outputs") is not None:
            updated_state["intermediate_outputs"]["planning_details"] = {
                "classification": output_data.get(PLANNING_CLASSIFICATION),
                "reasoning": output_data.get(PLANNING_REASONING),
                "plan_size": len(output_data.get(RESEARCH_PLAN, [])),
                "has_direct_answer": output_data.get(DIRECT_ANSWER) is not None
            }
        
        # Set quality metrics if we have a direct answer
        if output_data.get(DIRECT_ANSWER):
            updated_state["confidence_score"] = 0.85  # High confidence for direct answers
        
        return updated_state 