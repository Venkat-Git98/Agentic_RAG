"""
Planning Agent for LangGraph workflow.

This agent uses a focused PlanningTool to decompose a complex query into a
series of logical, targeted sub-queries for research.
"""

import re
from typing import Dict, Any

from .base_agent import BaseLangGraphAgent
from state import AgentState
from state_keys import (
    USER_QUERY, CONTEXT_PAYLOAD, CURRENT_STEP, RESEARCH_PLAN,
    PLANNING_REASONING, INTERMEDIATE_OUTPUTS, MATH_CALCULATION_NEEDED
)
from tools.planning_tool import PlanningTool


class PlanningAgent(BaseLangGraphAgent):
    """
    A focused Planning Agent that decomposes a complex query into a research plan.
    """
    
    def __init__(self):
        """Initialize the Planning Agent."""
        super().__init__(model_tier="tier_1", agent_name="PlanningAgent")
        self.planning_tool = PlanningTool()
    
    def _detect_calculation_query(self, query: str) -> bool:
        """
        Detect if query requires mathematical calculations.
        
        Args:
            query: The user query to analyze
            
        Returns:
            True if the query requires calculations, False otherwise
        """
        calculation_patterns = [
            r'calculate|compute|equation|formula',
            r'what is the.*value|final.*load|reduced.*load',
            r'equation\s+\d+[-\.]?\d*|formula\s+\d+[-\.]?\d*',
            r'psf|sq\s*ft|tributary\s*area|live\s*load',
            r'apply.*equation|using.*equation|with.*equation',
            r'step[-\s]*by[-\s]*step|show.*work|perform.*calculation'
        ]
        
        for pattern in calculation_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                self.logger.info(f"Calculation query detected with pattern: {pattern}")
                return True
        
        return False
    
    async def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        Executes the planning logic by calling the specialized PlanningTool.
        
        Args:
            state: Current workflow state.
            
        Returns:
            A dictionary containing the research plan and reasoning.
        """
        user_query = state[USER_QUERY]
        context_payload = state.get(CONTEXT_PAYLOAD, "")
        
        self.logger.info(f"Generating research plan for query: '{user_query[:100]}...'")
        
        # Detect if this is a calculation query
        is_calculation_query = self._detect_calculation_query(user_query)
        if is_calculation_query:
            self.logger.info("🧮 Calculation query detected - will use enhanced synthesis")
        
        try:
            # The planning tool is now specialized and only returns a plan and reasoning.
            planning_result = self.planning_tool(
                query=user_query,
                context_payload=context_payload
            )
            
            self.logger.info(f"Successfully generated a research plan with {len(planning_result.get('plan', []))} steps.")
            
            result = {
                PLANNING_REASONING: planning_result.get("reasoning"),
                "reasoning": planning_result.get("reasoning"), # Add this for the wrapper
                RESEARCH_PLAN: planning_result.get("plan", [])
            }
            
            # Add calculation flag if detected
            if is_calculation_query:
                result[MATH_CALCULATION_NEEDED] = True
                result["calculation_context"] = {
                    "equation_detected": True,
                    "variables_needed": True,
                    "numerical_result_required": True
                }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Critical error in planning tool execution: {e}", exc_info=True)
            # Fallback to a basic plan if the tool fails catastrophically.
            return {
                PLANNING_REASONING: f"Planning tool failed with error: {e}. Falling back to a single-step plan.",
                "reasoning": f"Planning tool failed with error: {e}. Falling back to a single-step plan.", # Add this
                RESEARCH_PLAN: [user_query]
            }
    
    def _validate_agent_specific_state(self, state: AgentState) -> None:
        """
        Validates the necessary state for the Planning Agent.
        
        Args:
            state: The current workflow state.
        """
        if not state.get(USER_QUERY):
            raise ValueError("user_query is required for the planning agent.")
    
    def _apply_agent_specific_updates(self, state: AgentState, output_data: Dict[str, Any]) -> AgentState:
        """
        Applies the planning output to the workflow state.
        
        Args:
            state: The current workflow state.
            output_data: The output from the execute method.
            
        Returns:
            The updated workflow state.
        """
        updated_state = state.copy()
        updated_state.update(output_data)

        # Log the planner's reasoning.
        if output_data.get(PLANNING_REASONING):
            intermediate_log = updated_state.get(INTERMEDIATE_OUTPUTS, [])
            if not isinstance(intermediate_log, list):
                intermediate_log = []
            intermediate_log.append({
                "step": "planning",
                "agent": self.agent_name,
                "log": output_data[PLANNING_REASONING]
            })
            updated_state[INTERMEDIATE_OUTPUTS] = intermediate_log

        # The next step after planning is always to create the HyDE documents.
        updated_state[CURRENT_STEP] = "hyde_generation"
        
        return updated_state 