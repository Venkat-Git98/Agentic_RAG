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
        user_query = state["user_query"]
        context_payload = state.get("context_payload", "")
        
        # Use triage classification if available, otherwise use planning classification
        classification = state.get("triage_classification") or state.get("planning_classification")
        
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
                "planning_classification": "engage",
                "planning_reasoning": f"Planning tool error: {str(e)}, falling back to engage",
                "research_plan": [{
                    "sub_query": user_query,
                    "hyde_document": f"Fallback research for: {user_query}"
                }],
                "current_step": "research",
                "workflow_status": "running"
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
                "planning_classification": "simple_answer",
                "planning_reasoning": "Planning tool provided direct answer",
                "direct_answer": planning_result.get("direct_answer", "Direct answer provided."),
                "current_step": "finish",
                "workflow_status": "completed"
            }
        
        elif classification == "engage":
            # Complex query requiring research
            plan = planning_result.get("plan", [])
            
            if not plan:
                self.logger.warning("Engage classification but no plan provided, creating fallback")
                plan = [{
                    "sub_query": state["user_query"],
                    "hyde_document": f"Research the following question from the Virginia Building Code: {state['user_query']}"
                }]
            
            return {
                "planning_classification": "engage",
                "planning_reasoning": planning_result.get("reasoning", "Complex query requiring research"),
                "research_plan": plan,
                "current_step": "research",
                "workflow_status": "running"
            }
        
        elif classification == "direct_retrieval":
            # Direct entity lookup (handled by planning tool's internal logic)
            return {
                "planning_classification": "direct_retrieval", 
                "planning_reasoning": planning_result.get("reasoning", "Direct entity retrieval"),
                "direct_answer": planning_result.get("direct_answer", "Entity retrieved successfully."),
                "direct_retrieval_entity": {
                    "entity_type": planning_result.get("entity_type", "unknown"),
                    "entity_id": planning_result.get("entity_id", "unknown")
                },
                "current_step": "finish",
                "workflow_status": "completed"
            }
        
        else:
            # Unknown classification, default to engage
            self.logger.warning(f"Unknown classification '{classification}', defaulting to engage")
            return {
                "planning_classification": "engage",
                "planning_reasoning": f"Unknown classification '{classification}', defaulting to research",
                "research_plan": [{
                    "sub_query": state["user_query"],
                    "hyde_document": f"Research the following question: {state['user_query']}"
                }],
                "current_step": "research", 
                "workflow_status": "running"
            }
    
    def _validate_agent_specific_state(self, state: AgentState) -> None:
        """
        Validates planning agent specific state requirements.
        
        Args:
            state: State to validate
            
        Raises:
            ValueError: If required fields are missing
        """
        if not state.get("user_query"):
            raise ValueError("user_query is required for planning")
        
        # Check that we're in the right step
        if state.get("current_step") not in ["planning", "triage"]:
            self.logger.warning(f"Unexpected current_step '{state.get('current_step')}' for planning agent")
    
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
                "classification": output_data.get("planning_classification"),
                "reasoning": output_data.get("planning_reasoning"),
                "plan_size": len(output_data.get("research_plan", [])),
                "has_direct_answer": output_data.get("direct_answer") is not None
            }
        
        # Set quality metrics if we have a direct answer
        if output_data.get("direct_answer"):
            updated_state["confidence_score"] = 0.85  # High confidence for direct answers
        
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
        
        Args:
            state: Current workflow state
            
        Returns:
            Dictionary containing enhanced planning results
        """
        # First try the enhanced strategies
        enhanced_result = await self._try_enhanced_strategies(state)
        if enhanced_result:
            return enhanced_result
        
        # Fall back to original planning logic
        return await super().execute(state)
    
    async def _try_enhanced_strategies(self, state: AgentState) -> Dict[str, Any]:
        """
        Tries enhanced planning strategies for specific query types.
        
        Args:
            state: Current workflow state
            
        Returns:
            Enhanced planning result if applicable, None otherwise
        """
        user_query = state["user_query"].lower()
        
        # Check for calculation queries
        if any(word in user_query for word in ["calculate", "formula", "equation", "compute"]):
            return await self._handle_calculation_query(state)
        
        # Check for comparison queries
        if any(word in user_query for word in ["compare", "difference", "versus", "vs"]):
            return await self._handle_comparison_query(state)
        
        # Check for requirement queries
        if any(word in user_query for word in ["requirements", "required", "must", "shall"]):
            return await self._handle_requirement_query(state)
        
        # Check for compliance queries
        if any(word in user_query for word in ["comply", "compliance", "meets", "satisfies"]):
            return await self._handle_compliance_query(state)
        
        return None
    
    async def _handle_calculation_query(self, state: AgentState) -> Dict[str, Any]:
        """Handles calculation-specific queries with enhanced planning."""
        return {
            "planning_classification": "engage",
            "planning_reasoning": "Calculation query detected - enhanced planning for formulas and variables",
            "research_plan": [
                {
                    "sub_query": f"What is the specific formula or equation for: {state['user_query']}",
                    "hyde_document": "The Virginia Building Code provides specific formulas and equations for structural calculations. The formula typically includes variables such as load factors, material properties, and geometric parameters."
                },
                {
                    "sub_query": f"What are the variable definitions and units for: {state['user_query']}",
                    "hyde_document": "Building code formulas require precise definition of variables including units, acceptable ranges, and calculation methods."
                }
            ],
            "current_step": "research",
            "workflow_status": "running"
        }
    
    async def _handle_comparison_query(self, state: AgentState) -> Dict[str, Any]:
        """Handles comparison queries with enhanced planning."""
        return {
            "planning_classification": "engage", 
            "planning_reasoning": "Comparison query detected - enhanced planning for multiple entities",
            "research_plan": [
                {
                    "sub_query": f"First component of comparison: {state['user_query']}",
                    "hyde_document": "Building code sections provide specific requirements, conditions, and applications for different structural elements and building types."
                },
                {
                    "sub_query": f"Second component of comparison: {state['user_query']}",
                    "hyde_document": "Comparative analysis requires understanding the specific requirements, limitations, and applications defined in the building code."
                }
            ],
            "current_step": "research",
            "workflow_status": "running"
        }
    
    async def _handle_requirement_query(self, state: AgentState) -> Dict[str, Any]:
        """Handles requirement-specific queries."""
        return {
            "planning_classification": "engage",
            "planning_reasoning": "Requirements query detected - enhanced planning for regulatory content",
            "research_plan": [
                {
                    "sub_query": f"Specific requirements for: {state['user_query']}",
                    "hyde_document": "The Virginia Building Code establishes specific requirements including minimum standards, conditions for application, and compliance criteria."
                }
            ],
            "current_step": "research",
            "workflow_status": "running"
        }
    
    async def _handle_compliance_query(self, state: AgentState) -> Dict[str, Any]:
        """Handles compliance checking queries."""
        return {
            "planning_classification": "engage",
            "planning_reasoning": "Compliance query detected - enhanced planning for code verification",
            "research_plan": [
                {
                    "sub_query": f"Compliance requirements and criteria for: {state['user_query']}",
                    "hyde_document": "Building code compliance requires meeting specific criteria, following prescribed methods, and satisfying regulatory requirements as outlined in the Virginia Building Code."
                }
            ],
            "current_step": "research",
            "workflow_status": "running"
        } 