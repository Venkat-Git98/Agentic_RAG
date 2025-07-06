"""
Router Agent for LangGraph workflow.

This agent is the first step in the workflow. Its sole responsibility is to
classify the user's query into one of three categories to determine the
correct downstream path.
"""

import json
import re
from typing import Dict, Any

from .base_agent import BaseLangGraphAgent
from state import AgentState

class RouterAgent(BaseLangGraphAgent):
    """
    A simple, focused agent that classifies incoming queries.
    """
    
    def __init__(self):
        """Initialize the Router Agent with Tier 2 model for speed."""
        super().__init__(model_tier="tier_2", agent_name="RouterAgent")

    async def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        Classifies the user's query.
        """
        user_query = state["user_query"].strip()
        self.logger.info(f"Routing query: {user_query[:100]}...")

        prompt = f"""
You are a routing specialist for an AI system that answers questions about the Virginia Building Code.
Your only job is to classify the user's query into one of three categories.

**Classification Options:**
1.  `direct_retrieval`: For queries that ask for a specific, uniquely identifiable entity.
    *   Examples: "Explain Section 1609.1.1", "Show me Table 1604.3", "Summarize Chapter 16".

2.  `clarification`: For queries that are on-topic but are too vague, ambiguous, or incomplete to be actionable.
    *   Examples: "What about structural integrity?", "Tell me about the code.", "Explain Section 1611.1 and its accompanying diagram."

3.  `research`: For any other complex query that requires reasoning, comparison, or a multi-step research process.
    *   Examples: "What are the requirements for high-rise buildings?", "Compare wind load requirements in coastal vs. non-coastal zones.", "Explain the methodology for calculating roof rainwater load."

**User Query:**
{user_query}

**Your Response (JSON only):**
{{
    "classification": "direct_retrieval|clarification|research"
}}
"""
        
        try:
            response_text = await self.generate_content_async(prompt)
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not json_match:
                self.logger.warning("No JSON found in router response, defaulting to research.")
                return {"routing_classification": "research"}
            
            result = json.loads(json_match.group(0))
            classification = result.get("classification")

            if classification not in ["direct_retrieval", "clarification", "research"]:
                self.logger.warning(f"Invalid classification '{classification}', defaulting to research.")
                return {"routing_classification": "research"}
            
            self.logger.info(f"Routing classification: {classification}")
            return {"routing_classification": classification}

        except Exception as e:
            self.logger.error(f"Error in RouterAgent: {e}", exc_info=True)
            return {"routing_classification": "research"} 