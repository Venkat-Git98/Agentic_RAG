"""
Triage Agent for LangGraph workflow.

This agent performs the initial classification of user queries to determine
the appropriate routing through the workflow.
"""

import os
import json
import re
from typing import Dict, Any

from .base_agent import BaseLangGraphAgent
from state import AgentState
from state_keys import (
    TRIAGE_CLASSIFICATION, REWRITTEN_QUERY, TRIAGE_REASONING,
    USER_QUERY, CURRENT_STEP, WORKFLOW_STATUS,
    INTERMEDIATE_OUTPUTS, FINAL_ANSWER
)
from prompts import TRIAGE_PROMPT


class TriageAgent(BaseLangGraphAgent):
    """
    Triage Agent for initial query classification.
    
    This agent acts as a sophisticated router, determining the most efficient
    path for a user's query based on its content and conversational context.
    """
    
    def __init__(self):
        """Initialize the Triage Agent with Tier 2 model for fast classification."""
        super().__init__(model_tier="tier_2", agent_name="TriageAgent")
    
    async def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute the triage classification logic.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dictionary containing classification results
        """
        user_query = state.get(USER_QUERY, "").strip()
        context_payload = state.get("context_payload", "")
        
        self.logger.info(f"Triaging query: '{user_query[:100]}...'")
        
        # Use LLM for sophisticated classification
        llm_classification = await self._llm_classification(user_query, context_payload)
        
        self.logger.info(f"LLM classification result: {llm_classification.get('classification')}")
        
        # The output of execute should be a dictionary that can be directly updated into the state
        # The keys should match the state keys for clarity.
        return {
            TRIAGE_CLASSIFICATION: llm_classification.get("classification"),
            REWRITTEN_QUERY: llm_classification.get("rewritten_query", user_query),
            TRIAGE_REASONING: llm_classification.get("reasoning"),
            "triage_confidence": llm_classification.get("confidence", 0.8),
            "direct_response": llm_classification.get("direct_response")
        }
    
    async def _llm_classification(self, query: str, context_payload: str) -> Dict[str, Any]:
        """
        Uses an LLM for sophisticated query classification and routing.
        
        Args:
            query: User query string
            context_payload: Context from conversation manager, including previous turns.
            
        Returns:
            A dictionary with the classification, reasoning, and potentially a rewritten query.
        """
        prompt = TRIAGE_PROMPT.format(
            conversation_history=context_payload if context_payload else "No previous context available.",
            user_query=query
        )
        
        try:
            response_text = await self.generate_content_async(prompt)
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not json_match:
                self.logger.warning("No JSON found in LLM response, defaulting to complex_research")
                return {
                    "classification": "complex_research",
                    "reasoning": "Failed to parse LLM response, defaulting to complex_research for safety.",
                    "confidence": 0.5
                }
            
            result = json.loads(json_match.group(0))
            
            # Validate classification
            valid_classifications = ["simple_response", "contextual_clarification", "direct_retrieval", "complex_research", "clarify_and_rewrite"]
            if result.get("classification") not in valid_classifications:
                self.logger.warning(f"Invalid classification '{result.get('classification')}', defaulting to complex_research")
                result["classification"] = "complex_research"
                result["reasoning"] = f"Invalid classification '{result.get('classification')}' detected, defaulting to complex_research"
            
            return result
            
        except (json.JSONDecodeError, Exception) as e:
            self.logger.error(f"Error in LLM classification: {e}")
            return {
                "classification": "complex_research",
                "reasoning": f"Classification error: {str(e)}, defaulting to complex_research",
                "confidence": 0.5
            }
    
    def _validate_agent_specific_state(self, state: AgentState) -> None:
        """
        Validates triage agent specific state requirements.
        
        Args:
            state: State to validate
            
        Raises:
            ValueError: If required fields are missing
        """
        if not state.get(USER_QUERY):
            raise ValueError("user_query is required for triage")
    
    def _apply_agent_specific_updates(self, state: AgentState, output_data: Dict[str, Any]) -> AgentState:
        """
        Applies triage-specific state updates.
        
        Args:
            state: Current state
            output_data: Triage output data
            
        Returns:
            Updated state
        """
        updated_state = state.copy()
        updated_state.update(output_data)

        # Log the reasoning
        if updated_state.get(TRIAGE_REASONING):
            intermediate_log = updated_state.get(INTERMEDIATE_OUTPUTS, [])
            if not isinstance(intermediate_log, list):
                intermediate_log = []
            intermediate_log.append({
                "step": "triage",
                "agent": self.agent_name,
                "log": updated_state[TRIAGE_REASONING]
            })
            updated_state[INTERMEDIATE_OUTPUTS] = intermediate_log

        # Determine the next step based on classification
        classification = output_data.get(TRIAGE_CLASSIFICATION)
        
        if classification == "simple_response":
            updated_state[WORKFLOW_STATUS] = "completed"
            updated_state[FINAL_ANSWER] = output_data.get("direct_response", "I'm sorry, I couldn't process that request.")
        elif classification == "contextual_clarification":
            updated_state[CURRENT_STEP] = "contextual_answering"
        else:  # direct_retrieval, complex_research, clarify_and_rewrite
            updated_state[CURRENT_STEP] = "planning"
            if classification == "clarify_and_rewrite" and output_data.get(REWRITTEN_QUERY):
                updated_state[USER_QUERY] = output_data[REWRITTEN_QUERY]
        
        return updated_state 