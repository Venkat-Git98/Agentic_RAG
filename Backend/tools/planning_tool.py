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
        
        # Specialist prompt for calculation queries
        self.SPECIALIST_CALCULATION_PROMPT = """
You are a Specialist Planner for an AI agent that answers building code questions requiring mathematical calculations or step-by-step procedures.
Your primary goal is to analyze the user's query and create a detailed, granular research plan that ensures all necessary formulas, variables, and calculation steps are retrieved and executed.

**CRITICAL RULE: For calculation queries, your plan MUST include:**
- A sub-query to retrieve the exact formula or equation (with section reference if possible)
- Sub-queries to extract all required variables, definitions, and conditions
- A sub-query to perform the calculation using the retrieved formula and variables (if values are provided)
- Any additional steps needed to clarify applicability, exceptions, or special cases

**Your Thought Process:**
1. Break down the calculation into all required components: formula, variables, conditions, and calculation steps.
2. For each component, write a specific sub-query that will retrieve or compute the needed information.
3. Ensure the plan is step-by-step and leaves nothing ambiguous for the calculation agent.

**Example for a Calculation Query:**
User Query: "How do I calculate the reduced live load for a floor using Equation 16-7?"
Your JSON Response:
```json
{{
  "reasoning": "The user is asking for a step-by-step calculation using Equation 16-7. I need to retrieve the equation, define all variables, get the required values, and then perform the calculation.",
  "plan": [
    {{
      "sub_query": "Retrieve Equation 16-7 for reduced live load calculation, including its section reference.",
      "hyde_document": "Equation 16-7 in Section 1607.12.1 provides the formula for reduced live load calculation."
    }},
    {{
      "sub_query": "Extract and define all variables used in Equation 16-7, including their units and conditions.",
      "hyde_document": "Variables in Equation 16-7 include L, K_LL, A_T, A_1, etc., as defined in Section 1607.12.1."
    }},
    {{
      "sub_query": "Gather the required values for each variable for the user's scenario (if provided).",
      "hyde_document": "Values for L, K_LL, A_T, and A_1 must be determined based on the floor area and occupancy."
    }},
    {{
      "sub_query": "Perform the reduced live load calculation using the retrieved formula and values.",
      "hyde_document": "The calculation will use Equation 16-7 and the gathered values to compute the reduced live load." 
    }}
  ]
}}
```
**CRITICAL: Your response must be only the JSON object, with no additional text or formatting.**
**INPUTS:**
- **Conversation Context:**
{context_payload}
- **User Query:**
{user_query}

**Your JSON Response:**
"""
        # Strategist prompt for research queries (moved from __call__)
        self.STRATEGIST_PROMPT = """
You are a Master Strategist for an AI agent that answers questions about the Virginia Building Code.
Your goal is to create an efficient, high-level research plan, not a long list of questions.

**CRITICAL RULE: The final plan MUST contain between 2 and 4 high-level, strategic sub-queries.**

**Your Thought Process (MUST follow this two-pass process):**

**Pass 1: Brainstorm (Internal Monologue)**
First, think about all the granular, specific questions you would need to answer to fully resolve the user's query. Consider all the different facets and sub-topics. (e.g., "For a staircase, I need to know about width, height, riser height, tread depth, handrail requirements, guardrail requirements, materials, etc.")

**Pass 2: Consolidate & Strategize (Your 'reasoning' output)**
Next, analyze your brainstormed list and group the questions into 2-4 high-level thematic clusters. Your goal is to create sub-queries that aim to retrieve the *table of contents* or *overview* for the main chapters that contain your brainstormed topics. This is more efficient than asking each granular question individually.

**Example of the Two-Pass Process:**

**User Query:** "What are the structural requirements for a multi-story hospital with a cast-in-place concrete frame, especially regarding tying floors and beams to columns?"

**Your Thought Process (Output as 'reasoning'):**
"My initial brainstorm of granular questions includes: what defines a hospital as a 'critical facility'?, what are the general structural design rules?, what specific rules apply to concrete?, what are the rules for tying elements together?, what are the seismic requirements for this?, what are the inspection requirements?

I will now consolidate these into a strategic, high-level plan. I see three main themes:
1.  **Classification & High-Level Rules:** I need to find out what a 'critical facility' is and the general structural rules that apply. This is likely in the 'Use and Occupancy' and 'Structural Design' chapters.
2.  **Specific Concrete Rules:** The core of the question is about concrete frames and connections. I need to find the main 'Concrete' chapter.
3.  **Inspections:** Finally, I need to find the rules for special inspections for this type of structure.

This leads to a concise, 3-step strategic plan."

**CRITICAL OUTPUT FORMAT (JSON ONLY):**
Your response MUST be a single JSON object with EXACTLY these keys:
- "reasoning": Your detailed, step-by-step thought process, showing how you consolidated granular questions into a strategic plan.
- "plan": A list of 2-4 high-level, strategic sub-queries.

**Example JSON Response (for the query above):**
```json
{{
  "reasoning": "My initial brainstorm of granular questions includes: what defines a hospital as a 'critical facility'?, what are the general structural design rules?, what specific rules apply to concrete?, what are the rules for tying elements together?, what are the seismic requirements for this?, what are the inspection requirements?\\n\\nI will now consolidate these into a strategic, high-level plan. I see three main themes:\\n1.  **Classification & High-Level Rules:** I need to find out what a 'critical facility' is and the general structural rules that apply. This is likely in the 'Use and Occupancy' and 'Structural Design' chapters.\\n2.  **Specific Concrete Rules:** The core of the question is about concrete frames and connections. I need to find the main 'Concrete' chapter.\\n3.  **Inspections:** Finally, I need to find the rules for special inspections for this type of structure.\\n\\nThis leads to a concise, 3-step strategic plan.",
  "plan": [
    "Retrieve the table of contents and overview for the chapters covering 'Use and Occupancy Classification' and 'Structural Design' to identify rules for critical facilities.",
    "Retrieve the table of contents and overview for the main 'Concrete' chapter to find rules for cast-in-place frames and connections.",
    "Retrieve the table of contents and overview for the chapter on 'Special Inspections and Tests'."
  ]
}}
```
**CRITICAL: Your response must be only the JSON object, with no additional text or formatting.**
**INPUTS:**
- **Conversation Context:**
{context_payload}
- **User Query:**
{user_query}

**Your JSON Response:**
"""

    def _is_calculation_query(self, query: str) -> bool:
        """
        Simple keyword-based detection for calculation queries.
        Returns True if the query is likely a calculation query.
        """
        query_lower = query.lower()
        calculation_keywords = [
            "calculate", "calculation", "compute", "determine", "evaluate", "solve", "formula", "equation", "step-by-step", "steps", "how do i calculate", "how to calculate"
        ]
        return any(kw in query_lower for kw in calculation_keywords)

    def __call__(self, query: str, context_payload: str) -> dict:
        """
        Executes the planning logic to generate sub-queries.
        """
        logging.info("Executing Planning Tool for complex research...")

        # Select planning mode
        if self._is_calculation_query(query):
            prompt_template = self.SPECIALIST_CALCULATION_PROMPT
            self.logger.info("Planning mode: SPECIALIST (calculation query detected)")
        else:
            prompt_template = self.STRATEGIST_PROMPT
            self.logger.info("Planning mode: STRATEGIST (research query detected)")

        prompt = prompt_template.format(context_payload=context_payload, user_query=query)

        response_text = None
        try:
            model = genai.GenerativeModel(TIER_1_MODEL_NAME)
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