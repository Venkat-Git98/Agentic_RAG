"""
Contextual Answering Agent

This agent is designed for a specific "fast path" in the workflow. It's
triggered when the TriageAgent identifies a user query as a direct,
context-dependent clarification of the previous turn's answer.
"""

import os
import json
import re
from typing import Dict, Any

from .base_agent import BaseLangGraphAgent
from core.state import AgentState
from state_keys import (
    USER_QUERY, FINAL_ANSWER, WORKFLOW_STATUS,
    INTERMEDIATE_OUTPUTS, CURRENT_STEP, CONTEXTUAL_ANSWER
)

class ContextualAnsweringAgent(BaseLangGraphAgent):
    """
    An agent that answers questions based only on the immediate context
    of the last conversation turn.
    """
    
    def __init__(self):
        """
        Initializes the agent with a Tier 1 model for high-quality,
        context-aware responses.
        """
        super().__init__(model_tier="tier_1", agent_name="ContextualAnsweringAgent")
        
    async def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        Executes the contextual answering logic.
        
        Args:
            state: The current workflow state.
            
        Returns:
            A dictionary with the final answer or a failure signal.
        """
        user_query = state.get(USER_QUERY, "").strip()
        context_payload = state.get("context_payload", "")
        
        self.logger.info(f"Attempting contextual answer for query: '{user_query[:100]}...'")
        
        if not context_payload:
            self.logger.warning("ContextualAnsweringAgent called without context. Cannot proceed.")
            return {
                "contextual_answer_success": False,
                "reasoning": "No context was provided to answer from."
            }
            
        llm_response = await self._generate_contextual_answer(user_query, context_payload)
        
        if llm_response.get("answerable"):
            self.logger.info("Successfully generated a contextual answer.")
            return {
                FINAL_ANSWER: llm_response.get("answer"),
                "contextual_answer_success": True,
                "reasoning": llm_response.get("reasoning")
            }
        else:
            self.logger.info("Could not answer from context. Rerouting to standard workflow.")
            return {
                "contextual_answer_success": False,
                "reasoning": llm_response.get("reasoning")
            }

    async def _generate_contextual_answer(self, query: str, context: str) -> Dict[str, Any]:
        """
        Uses a Tier-1 LLM to answer a query based *only* on provided context.
        
        Args:
            query: The user's follow-up question.
            context: The context from the previous conversational turn.
            
        Returns:
            A dictionary indicating success and containing the answer, or failure.
        """
        prompt = f'''
You are a specialized AI assistant with a single, critical task: answer the user's question based *only* on the provided "Conversation History".

**Your Strict Rules:**
1.  You MUST NOT use any external knowledge. Your entire universe is the text provided in the "Conversation History".
2.  If you can formulate a direct and accurate answer from the history, you must do so.
3.  If the history does not contain the information needed to answer the question, you MUST indicate that you cannot answer.

**Conversation History:**
---
{context}
---

**User's Question:**
"{query}"

**Your Task:**
Review the conversation history and the user's question. Respond in the following JSON format ONLY.

**JSON Output Format:**
{{
    "reasoning": "A step-by-step thought process of how you evaluated the context against the question.",
    "answerable": [true if you can answer from the context, false if you cannot],
    "answer": "[Your complete and accurate answer here. If 'answerable' is false, this should be an empty string.]"
}}
'''
        
        try:
            response_text = await self.generate_content_async(prompt)
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not json_match:
                self.logger.warning("No JSON found in contextual answer response.")
                return {"answerable": False, "reasoning": "Failed to parse LLM response."}
            
            return json.loads(json_match.group(0))
            
        except (json.JSONDecodeError, Exception) as e:
            self.logger.error(f"Error in contextual answer generation: {e}")
            return {"answerable": False, "reasoning": f"Error during generation: {e}"}
            
    def _validate_agent_specific_state(self, state: AgentState) -> None:
        """Validates state for this agent."""
        if not state.get(USER_QUERY):
            raise ValueError("user_query is required.")
        if not state.get("context_payload"):
            self.logger.warning("CONTEXTUAL_PAYLOAD is missing, which is highly unusual for this agent.")

    def _apply_agent_specific_updates(self, state: AgentState, output_data: Dict[str, Any]) -> AgentState:
        """Applies updates to the state."""
        updated_state = state.copy()
        updated_state.update(output_data)
        
        # Log reasoning
        if output_data.get("reasoning"):
            intermediate_log = updated_state.get(INTERMEDIATE_OUTPUTS, [])
            if not isinstance(intermediate_log, list):
                intermediate_log = []
            intermediate_log.append({
                "step": "contextual_answering",
                "agent": self.agent_name,
                "log": output_data["reasoning"]
            })
            updated_state[INTERMEDIATE_OUTPUTS] = intermediate_log

        if output_data.get("contextual_answer_success"):
            updated_state[WORKFLOW_STATUS] = "completed"
        else:
            # If it fails, we need to re-route to the main planning agent
            self.logger.info("Contextual answer failed, routing to planning step.")
            updated_state[CURRENT_STEP] = "planning"
            
        return updated_state 