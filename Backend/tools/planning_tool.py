"""
Implements the focused Planning Tool for the agentic workflow.
"""
import logging
import json
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from react_agent.base_tool import BaseTool
from config import TIER_1_MODEL_NAME
import re
from typing import Any, Dict

# Configure logging
logging.basicConfig(level=logging.INFO)

class PlanningTool(BaseTool):
    """
    A tool that decomposes a complex user query into a series of logical sub-queries.
    This tool is triggered when the TriageAgent classifies a query as 'complex_research'.
    """

    @property
    def name(self) -> str:
        return "create_research_plan"

    @property
    def description(self) -> str:
        return (
            "Analyzes a complex user's query and breaks it down into a series of "
            "logical, targeted sub-queries to guide the research process. "
            "Input: {'query': 'The user's question.', 'context_payload': 'The conversation history.'}"
        )

    def __init__(self):
        """Initializes the PlanningTool."""
        self.logger = logging.getLogger(self.__class__.__name__)

    def __call__(self, query: str, context_payload: str) -> dict:
        """
        Executes the planning logic to generate sub-queries.
        """
        logging.info("Executing Planning Tool for complex research...")

        # This prompt is focused solely on query decomposition for complex research.
        # Triage and HyDE generation are handled by other specialized agents.
        PLANNER_PROMPT = """
You are a master planner for an AI agent that answers questions about the Virginia Building Code.
Your sole responsibility is to take a complex user query and decompose it into a series of logical, targeted sub-queries that will drive the research process.

**Your Thought Process (Reasoning):**
First, you must externalize your thinking. Explain your strategy for breaking down the user's query. For example, "The user is asking about the requirements for a commercial staircase, which involves analyzing rules for geometry, materials, and handrails. I will create a sub-query for each of these aspects."

**CRITICAL SUB-QUERY GUIDELINES:**
- **Goal:** Each sub-query should be a self-contained question that can be answered by retrieving a specific section or a small set of related sections from the building code.
- **Specificity:** Be extremely specific. Target the exact information needed, not general concepts.
- **Formulas:** If the main query involves a calculation, create separate sub-queries to first retrieve the formula itself and then to find the definitions of its variables.
- **Requirements:** When asking about requirements, frame the sub-query to ask for specific conditions, thresholds, and applicability rules.
- **Anchor to Code:** Whenever the user's query mentions a specific section number, at least one of your sub-queries MUST be anchored to that exact section.

**INPUTS:**
- **Conversation Context:**
{context_payload}
- **User Query:**
{user_query}

**CRITICAL OUTPUT FORMAT (JSON ONLY):**
Your response MUST be a single JSON object with EXACTLY these keys:
- "reasoning": Your detailed, step-by-step thought process for creating the plan.
- "plan": A list of strings, where each string is a precise and targeted sub-query.

**Example JSON Response:**
```json
{{
  "reasoning": "The user is asking a multi-faceted question about the safety requirements for a commercial exit door. I need to break this down into its core components: the physical dimensions of the door, the hardware requirements (locks, handles), and the signage requirements.",
  "plan": [
    "What are the minimum width and height requirements for an exit door in a commercial building under the Virginia Building Code?",
    "What are the specific requirements for locks, latches, and panic hardware on commercial exit doors?",
    "What are the signage and illumination requirements for marking commercial exit doors?"
  ]
}}
```

**Your JSON Response:**
"""
        response_text = None
        try:
            model = genai.GenerativeModel(TIER_1_MODEL_NAME)
            prompt = PLANNER_PROMPT.format(context_payload=context_payload, user_query=query)
            
            self.logger.info("Generating research plan from LLM...")
            
            response = model.generate_content(prompt)
            response_text = response.text.strip()
            
            self.logger.info(f"Raw LLM planning response: {response_text}")
            
            json_match = re.search(r"```json\n(.*)```", response_text, re.DOTALL)
            if not json_match:
                json_text = response_text
            else:
                json_text = json_match.group(1).strip()

            plan_result = json.loads(json_text)
            
            if "plan" not in plan_result or "reasoning" not in plan_result:
                raise ValueError("LLM response is missing required 'plan' or 'reasoning' keys.")

            return plan_result

        except Exception as e:
            self.logger.error(f"Error during planning tool execution: {e}", exc_info=True)
            if response_text:
                self.logger.error(f"Response text that caused error: {response_text}")
            
            # Fallback to a safe plan
            return {
                "reasoning": f"An error occurred during planning: {e}. Falling back to a simple plan.",
                "plan": [query] # Fallback to using the original query as a single sub-query
            } 