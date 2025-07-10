"""
Planning Agent for LangGraph workflow.

This agent uses a focused PlanningTool to decompose a complex query into a
series of logical, targeted sub-queries for research.
"""

from typing import Dict, Any

from .base_agent import BaseLangGraphAgent
from state import AgentState
from state_keys import (
    USER_QUERY, CONTEXT_PAYLOAD, CURRENT_STEP, RESEARCH_PLAN,
    PLANNING_REASONING, INTERMEDIATE_OUTPUTS
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
        
        try:
            # The planning tool is now specialized and only returns a plan and reasoning.
            planning_result = self.planning_tool(
                query=user_query,
                context_payload=context_payload
            )
            
            self.logger.info(f"Successfully generated a research plan with {len(planning_result.get('plan', []))} steps.")
            
            return {
                PLANNING_REASONING: planning_result.get("reasoning"),
                RESEARCH_PLAN: planning_result.get("plan", [])
            }
            
        except Exception as e:
            self.logger.error(f"Critical error in planning tool execution: {e}", exc_info=True)
            # Fallback to a basic plan if the tool fails catastrophically.
            return {
                PLANNING_REASONING: f"Planning tool failed with error: {e}. Falling back to a single-step plan.",
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