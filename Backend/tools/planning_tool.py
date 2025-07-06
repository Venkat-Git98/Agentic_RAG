"""
Implements the consolidated Planning Tool for the ReAct Agent.
"""
import logging
import json
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from react_agent.base_tool import BaseTool
from config import TIER_2_MODEL_NAME, TIER_1_MODEL_NAME
from prompts import PLANNER_PROMPT
import re
import copy
from typing import Any, Dict

from tools.neo4j_connector import Neo4jConnector
from .image_utils import process_image_for_llm

# Configure logging
logging.basicConfig(level=logging.INFO)

# Tier 1 model for high-stakes planning
TIER_1_MODEL_NAME = "gemini-1.5-pro-latest"

# Custom prompts for the planner
from prompts import PLANNER_PROMPT

class PlanningTool(BaseTool):
    """
    A tool that performs three critical planning steps in one call:
    1. Triage: Decides if the query is relevant.
    2. Decompose: Breaks the query into sub-queries.
    3. HyDE: Generates a hypothetical document for each sub-query.
    """

    @property
    def name(self) -> str:
        return "create_research_plan"

    @property
    def description(self) -> str:
        return (
            "Analyzes a user's query to create a complete research plan. "
            "It classifies the query, and if relevant, breaks it down into sub-queries "
            "and generates a hypothetical document for each to guide retrieval. "
            "This should be the first tool called for any new user query. "
            "Input: {'query': 'The user's question.', 'context_payload': 'The conversation history.'}"
        )

    def __init__(self):
        """Initializes the PlanningTool."""
        self.logger = logging.getLogger(self.__class__.__name__)
        # Further initialization if needed

    def _sanitize_for_logging(self, data: Any) -> Any:
        """Recursively removes 'embedding' keys from a dictionary or list of dictionaries for cleaner logging."""
        if isinstance(data, dict):
            # Use copy to avoid modifying the original dictionary in place
            clean_data = {}
            for key, value in data.items():
                if key != 'embedding':
                    clean_data[key] = self._sanitize_for_logging(value)
            return clean_data
        elif isinstance(data, list):
            return [self._sanitize_for_logging(item) for item in data]
        else:
            return data

    def __call__(self, query: str, context_payload: str) -> dict:
        """
        Executes the full planning logic.
        """
        logging.info("Executing Planning Tool...")

        # --- WORKAROUND FOR PROMPTS.PY EDITING BUG ---
        # Manually define the correct planner prompt here to bypass file editing issues.
        IMPROVED_PLANNER_PROMPT = """
You are the master planner for an AI agent that answers questions about the Virginia Building Code.
Your primary goal is to analyze a user's query and create an optimal research strategy.

You have three choices for the `classification`:

1.  `clarify`: If the user's query is too vague, ambiguous, or lacks the necessary detail to be answerable.
    -   If you choose this, you MUST provide a `question_for_user` to ask for the missing information.

2.  `direct_retrieval`: If the user's query is a simple, direct lookup for a specific, uniquely identifiable entity like "show me section 1604.3" or "what is Table 1607.1?".
    -   You MUST provide the `entity_type` (e.g., "Subsection", "Table", "Section").
    -   You MUST provide the `entity_id` (e.g., "1604.3", "Table 1607.1").
    -   You MUST provide a `reasoning` string explaining why this is a direct retrieval.

3.  `engage`: For complex questions requiring research across multiple parts of the code.
    -   You MUST provide a `reasoning` string explaining your thought process.
    -   You MUST provide a `plan` with highly targeted sub-queries.

**CRITICAL SUB-QUERY GUIDELINES:**
- **ALWAYS anchor sub-queries to specific section numbers** when mentioned in the user query
- **Separate formula retrieval from calculation steps** - create distinct sub-queries for each
- **Be extremely specific** - target exact information needed, not general concepts
- **For formulas**: Ask specifically for the equation, variables, and conditions
- **For requirements**: Ask for specific conditions, thresholds, and applicability rules

**HYDE DOCUMENT GUIDELINES:**
- Write documents that mirror actual building code language and structure
- Use regulatory terminology: "shall", "permitted", "required", "in accordance with"
- Include specific section references and technical terms
- For formulas: Describe mathematical relationships and variable definitions in detail
- Match the hierarchical structure of building code sections

**CRITICAL OUTPUT FORMAT:**
For "engage" classification, your plan must be a list of objects with EXACTLY these keys:
- "sub_query": The specific question
- "hyde_document": The hypothetical document

**Example JSON for Live Load Query:**
```json
{{
  "classification": "engage",
  "reasoning": "Complex query requiring multiple research steps",
  "plan": [
    {{
      "sub_query": "According to Section 1607.12.1, what are the specific conditions and tributary area requirements for live load reduction in office buildings?",
      "hyde_document": "Section 1607.12.1 of the Virginia Building Code establishes the conditions under which live load reduction is permitted for structural members. The section specifies minimum tributary area requirements for different occupancy classifications, including office buildings."
    }}
  ]
}}
```

**Conversation Context:**
{context_payload}

**User Query:**
{user_query}

**Your JSON Response:**
"""
        # --- END WORKAROUND ---

        response_text = None
        try:
            # === LLM Call 1: Triage and Plan Generation ===
            model = genai.GenerativeModel(TIER_2_MODEL_NAME)
            prompt = IMPROVED_PLANNER_PROMPT.format(context_payload=context_payload, user_query=query)
            
            logging.info("Generating initial plan from LLM...")
            logging.info(f"Prompt being sent to LLM: {prompt[:500]}...")
            
            response = model.generate_content(prompt)
            response_text = response.text.strip()
            
            logging.info(f"Raw LLM response: {response_text}")  # Log full response for debugging
            
            # Use a more robust regex to find the JSON block
            json_match = re.search(r"```json\n(.*)```", response_text, re.DOTALL)
            if not json_match:
                # Fallback for models that don't use markdown fences
                json_text = response_text.strip()
            else:
                json_text = json_match.group(1).strip()

            plan_result = json.loads(json_text)
            classification = plan_result.get("classification")
            logging.info(f"LLM classification: {classification}")

            # === Clarification Logic ===
            if classification == "clarify":
                question = plan_result.get("question_for_user", "Could you please provide more details?")
                # We need to return this in a way that the dispatcher knows to halt and ask the user.
                # Let's adopt the 'simple_answer' structure for this.
                return {"classification": "simple_answer", "direct_answer": f"I need more information to proceed. {question}"}

            # === Direct Retrieval Logic ===
            if classification == "direct_retrieval":
                return self._retrieve_direct_entity(plan_result)

            # === Research Plan Logic (for 'engage') ===
            if classification == "engage":
                # The plan is already in the right format, so just return it
                return plan_result

            # If we fall through, something went wrong
            raise ValueError(f"Unhandled classification type: {classification}")

        except Exception as e:
            logging.error(f"Error during planning tool execution: {e}", exc_info=True)
            if response_text:
                logging.error(f"Response text that caused error: {response_text}")
            else:
                logging.error("No response text available")
            # Fallback to a safe engage plan
            return {
                "classification": "engage",
                "reasoning": f"An error occurred during planning: {e}",
                "plan": [{
                    "sub_query": query,
                    "hyde_document": f"An error occurred during planning. Fallback research for: {query}"
                }]
            }

    def _retrieve_direct_entity(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handles the direct retrieval of an entity from Neo4j.
        This function is now called by the guardrail as well.
        """
        entity_type = plan.get("entity_type")
        entity_id = plan.get("entity_id")

        # --- AUTO-CORRECTION GUARDRAIL ---
        if entity_type in ["Table", "Diagram"]:
            self.logger.warning(f"Correcting entity_type from '{entity_type}' to 'Subsection' to enforce system rule.")
            entity_type = "Subsection"
            plan["reasoning"] += " | [Auto-Correction]: The entity type was corrected to 'Subsection' as the system retrieves tables and diagrams via their parent section."

        self.logger.info(f"Performing direct lookup for {entity_type} with ID '{entity_id}'")
        try:
            # Get the singleton Neo4j connector instance
            # The get_driver() method returns the driver, not the connector class itself.
            # We need to call the static method on the class.
            
            # Use the connector to get the full text of the section and raw diagram data
            lookup_result = Neo4jConnector.direct_lookup(entity_type, entity_id)
            context = lookup_result.get("context")
            raw_diagrams = lookup_result.get("raw_diagrams", [])

            if not context:
                self.logger.warning(f"Direct retrieval for {entity_type} {entity_id} found no content.")
                return {
                    "classification": "engage", # Fallback to research if not found
                    "reasoning": f"Direct retrieval failed for {entity_type} {entity_id}. Falling back to research.",
                    "plan": [{
                        "sub_query": f"Find information about {entity_type} {entity_id}",
                        "hyde_document": f"Could not directly retrieve {entity_type} {entity_id}. Researching to find relevant information."
                    }]
                }
            
            self.logger.info(f"Successfully retrieved content for {entity_type} {entity_id}.")
            
            processed_diagrams = []
            if raw_diagrams:
                self.logger.info(f"Found {len(raw_diagrams)} associated diagrams. Processing them now...")
                for diagram_data in raw_diagrams:
                    # The 'path' key holds the full path to the image
                    image_path = diagram_data.get("path")
                    if image_path:
                        processed_image_data = process_image_for_llm(image_path)
                        if processed_image_data:
                            processed_diagrams.append({
                                "uid": diagram_data.get("uid"),
                                "description": diagram_data.get("description"),
                                "image_data": processed_image_data
                            })

            return {
                "classification": "direct_retrieval",
                "retrieved_context": context,
                "retrieved_diagrams": processed_diagrams # Return the processed data
            }

        except Exception as e:
            self.logger.error(f"Error during direct entity retrieval for {entity_type} {entity_id}: {e}", exc_info=True)
            return {
                "classification": "engage",
                "reasoning": f"An error occurred during direct retrieval for {entity_type} {entity_id}: {e}",
                "plan": [{
                    "sub_query": f"Find information about {entity_type} {entity_id}",
                    "hyde_document": f"An error occurred trying to retrieve {entity_type} {entity_id}. Researching as a fallback."
                }]
            } 