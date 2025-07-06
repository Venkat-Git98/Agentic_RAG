"""
New, specialized agent to determine the best retrieval strategy for a given sub-query.
"""
import json
import re
from typing import Dict, Any

from .base_agent import BaseLangGraphAgent
from state import AgentState

# This prompt is highly specific and guides the LLM to choose the best tool.
STRATEGY_SELECTION_PROMPT = """
You are a retrieval strategy expert for a building code AI. Your task is to select the single best tool to find the answer for the given sub-query.

**Available Tools:**

1.  `direct_subsection_lookup`: Use this for queries that contain a specific section or subsection number (e.g., "1607.1", "Chapter 5", "Section 101.2"). This is the fastest and most precise tool for targeted lookups.

2.  `keyword_retrieval`: Use this for queries that contain unique, specific technical terms, proper nouns, or phrases that are likely to have an exact match in the text (e.g., "fire-retardant-treated wood", "ASTM E119", "cross-laminated timber").

3.  `vector_search`: Use this for all other queries, especially conceptual or descriptive questions that rely on semantic meaning rather than exact keywords (e.g., "What is the intent of the egress code?", "summarize the requirements for accessibility").

**Decision Process:**
1.  Examine the sub-query for a section number. If present, choose `direct_subsection_lookup`.
2.  If no section number, look for unique, technical keywords. If present, choose `keyword_retrieval`.
3.  Otherwise, default to `vector_search`.

**Sub-query:**
"{sub_query}"

**Your JSON Response:**
Respond with a single, valid JSON object with two keys:
- "tool": One of ["direct_subsection_lookup", "keyword_retrieval", "vector_search"]
- "query": The argument for the chosen tool. For `direct_subsection_lookup` and `keyword_retrieval`, this is the extracted section number or keyword. For `vector_search`, this is the original sub-query.

**Example 1:**
Sub-query: "What are the live load requirements in Section 1607.12?"
{{
  "tool": "direct_subsection_lookup",
  "query": "1607.12"
}}

**Example 2:**
Sub-query: "What are the requirements for 'impact-resistant coverings'?"
{{
  "tool": "keyword_retrieval",
  "query": "impact-resistant coverings"
}}

**Example 3:**
Sub-query: "Explain the general principles of fire-resistance."
{{
  "tool": "vector_search",
  "query": "Explain the general principles of fire-resistance."
}}
"""

class RetrievalStrategyAgent(BaseLangGraphAgent):
    """
    This agent determines the optimal retrieval strategy for a given sub-query.
    """

    def __init__(self):
        super().__init__(model_tier="tier_2", agent_name="RetrievalStrategyAgent")

    async def execute(self, state: dict) -> dict:
        sub_query = state.get("current_sub_query")
        if not sub_query:
            return {"strategy": {"tool": "vector_search", "query": ""}} # Default fallback

        prompt = STRATEGY_SELECTION_PROMPT.format(sub_query=sub_query)
        response_text = await self.generate_content_async(prompt)

        try:
            # Extract JSON from the response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON object found in strategy response.")
            
            strategy = json.loads(json_match.group(0))
            
            # Validate the output
            if "tool" not in strategy or "query" not in strategy:
                raise ValueError("Strategy JSON is missing 'tool' or 'query' key.")
            
            return {"strategy": strategy}
            
        except (json.JSONDecodeError, ValueError) as e:
            self.logger.error(f"Failed to parse retrieval strategy: {e}. Defaulting to vector search.")
            # Default to a safe fallback if parsing fails
            return {"strategy": {"tool": "vector_search", "query": sub_query}} 