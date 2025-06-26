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

from tools.neo4j_connector import Neo4jConnector

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
            
            # More robust JSON extraction - handle multiple JSON blocks
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if not json_match:
                # Try to find JSON without curly braces (in case it's malformed)
                lines = response_text.split('\n')
                json_lines = [line for line in lines if '"classification"' in line or '"reasoning"' in line or '"plan"' in line]
                if json_lines:
                    logging.warning(f"Found potential JSON lines but no valid JSON block: {json_lines}")
                logging.error(f"Full response was: {response_text}")
                raise ValueError("Could not find a JSON object in the model's response for planning.")
            
            json_text = json_match.group(0)
            logging.info(f"Extracted JSON: {json_text}")
            
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
                entity_type = plan_result.get("entity_type")
                entity_id = plan_result.get("entity_id")
                
                # --- START DEBUG LOGGING ---
                logging.info(f"DEBUG: Extracted Entity Type: {entity_type} (Type: {type(entity_type)})")
                logging.info(f"DEBUG: Extracted Entity ID: {entity_id} (Type: {type(entity_id)})")
                # --- END DEBUG LOGGING ---

                if not entity_type or not entity_id:
                    logging.warning("Direct retrieval classified, but missing entity type/id.")
                    # Fallback to standard research plan
                    return {"classification": "engage", "reasoning": "Fallback from failed direct retrieval.", "plan": []}

                # === DB Call: Fetch the specific entity ===
                retrieved_data = Neo4jConnector.direct_lookup(entity_type, entity_id)

                # --- START DEBUG LOGGING ---
                logging.info(f"DEBUG: Raw data from direct_lookup: {retrieved_data}")
                # --- END DEBUG LOGGING ---

                if not retrieved_data or retrieved_data.get("error"):
                    logging.error(f"Failed to retrieve data for {entity_type} {entity_id}.")
                    # Return a user-facing error message
                    return {
                        "classification": "simple_answer",
                        "direct_answer": f"I could not find the specific {entity_type.lower()} with ID '{entity_id}' in the knowledge base."
                    }

                # === LLM Call 2: Summarize the retrieved data ===
                # This gives a much more natural answer than just dumping the raw data.
                logging.info(f"Summarizing retrieved data for {entity_type} {entity_id}...")
                summarizer_model = genai.GenerativeModel(TIER_1_MODEL_NAME) # Use a powerful model for good summarization
                
                # Create a simple, readable format for the summarizer prompt
                context_str = json.dumps(retrieved_data, indent=2, default=str)
                
                # Add special instructions for ambiguous queries
                summarizer_reasoning = plan_result.get("reasoning", "")
                
                summarizer_prompt = (
                    f"The user asked the following query: '{query}'.\n"
                    f"The master planner provided this reasoning for the direct retrieval: '{summarizer_reasoning}'\n\n"
                    f"I have retrieved the following data from the knowledge base:\n"
                    f"--- DATA ---\n{context_str}\n--- END DATA ---\n\n"
                    "Please synthesize this data into a clear and direct answer to the user's query. "
                    "Use the planner's reasoning to focus on the most important part of the data for the user. "
                    "If the user's query was about a specific Table or Diagram, find that element in the 'child_nodes' or 'supplementary_content' of the data and feature it prominently in your answer, then provide the rest of the section as context."
                )
                
                summary_response = summarizer_model.generate_content(summarizer_prompt)
                
                return {
                    "classification": "simple_answer",
                    "direct_answer": summary_response.text.strip()
                }

            # If not direct retrieval, return the original plan
            logging.info(f"Proceeding with standard research plan. Classification: {classification}")
            return plan_result

        except Exception as e:
            logging.error(f"Error in PlanningTool: {e}")
            if response_text:
                logging.error(f"Raw response from LLM was: {response_text}")
            else:
                logging.error("No response text available")
            return {"classification": "error", "reasoning": str(e), "plan": []} 