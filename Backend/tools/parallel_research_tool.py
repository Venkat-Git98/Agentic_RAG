"""
Implements the parallelized Research and Sub-Answer Generation Tool.
"""
import logging
import asyncio
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import time

import google.generativeai as genai
from react_agent.base_tool import BaseTool
from config import EMBEDDING_MODEL, TIER_2_MODEL_NAME, TIER_1_MODEL_NAME
from tools.neo4j_connector import Neo4jConnector
from tools.reranker import Reranker
from state import RetrievedContext
from prompts import SUB_ANSWER_PROMPT, QUALITY_CHECK_PROMPT, SUBSECTION_EXTRACTION_PROMPT, RE_PLANNING_PROMPT
from neo4j.graph import Node
import json
from datetime import datetime
# --- Import the new tools ---
from tools.web_search_tool import TavilySearchTool
from tools.keyword_retrieval_tool import KeywordRetrievalTool
from .image_utils import process_image_for_llm
# --- Import the new strategy agent ---
from agents.retrieval_strategy_agent import RetrievalStrategyAgent

# --- Evaluation Logger Setup ---
# Create a dedicated logger for evaluation data
eval_logger = logging.getLogger('EvaluationLogger')
eval_logger.setLevel(logging.INFO)
# Prevent this logger from propagating to the root logger
eval_logger.propagate = False 
# Remove existing handlers to avoid duplicates during reloads
if eval_logger.hasHandlers():
    eval_logger.handlers.clear()
# Add a file handler to append to a jsonl file
eval_handler = logging.FileHandler('evaluation_log.jsonl')
eval_handler.setFormatter(logging.Formatter('%(message)s'))
eval_logger.addHandler(eval_handler)

# PROMPT FOR EXTRACTING ENTITIES FOR FALLBACK
EXTRACT_SECTION_ID_PROMPT_WITH_TYPE = """
Based on the user's sub-query, identify ALL primary Section or Subsection numbers being referenced.
Return the result as a JSON LIST of objects, with each object having two keys: "id" and "type".

**IMPORTANT RULES:**
- A "Section" is typically a whole number (e.g., 1607).
- A "Subsection" typically has a decimal (e.g., 1607.12, 1604.3.1).
- **IGNORE** any references to Equations (e.g., "Equation 16-7"), Tables (e.g., "Table 304.1"), or Figures. These are NOT sections or subsections.
- If no specific section or subsection number is mentioned, return an empty JSON list: [].

Example 1:
Sub-query: "What are the fire-resistance rating requirements in Section 703 and Subsection 704.1?"
JSON Output:
[
    {{"id": "703", "type": "Section"}},
    {{"id": "704.1", "type": "Subsection"}}
]

Example 2:
Sub-query: "What is the formula in Equation 16-7 and the live load factor from Table 1607.1?"
JSON Output:
[]

Sub-query: {sub_query}

JSON Output:
"""

# --- NEW RE-PLANNING PROMPT ---
RE_PLANNING_PROMPT = """
You are a Recovery Specialist agent. A sub-query has failed to retrieve sufficient context from the primary knowledge base.
Your task is to analyze the sub-query and decide the best recovery action from the available tools.

**Sub-query:** "{sub_query}"

**Available Tools:**
1.  `deep_graph_retrieval`: This is the most powerful tool. It performs a deep, hierarchical search of the knowledge base. It is best for queries that mention a specific Section or Subsection number (e.g., "1607.12", "Chapter 5").
2.  `keyword_retrieval`: This performs a direct keyword search. It is best for finding specific, but non-standard, terms or proper nouns that might not be captured well by semantic search (e.g., "Fire-resistance-Tabelle", "ASTM E119").
3.  `web_search`: This tool searches the public internet. It is the final resort, best used for queries that require up-to-the-minute information, external standards (like ACI or ASTM), or general engineering knowledge not present in the code.

**Your Decision Process:**
1.  Read the sub-query carefully.
2.  If it clearly references a Section or Subsection number, choose `deep_graph_retrieval`.
3.  If it contains a very specific, unique term or phrase, choose `keyword_retrieval`.
4.  If the query seems to ask for general knowledge, external standards, or if the other tools are unlikely to succeed, choose `web_search`.
5.  Based on your choice, generate the necessary input for the tool.

**Output Format:**
You MUST respond with a single, valid JSON object with two keys: "tool_to_use" and "query".
- `tool_to_use`: One of ["deep_graph_retrieval", "keyword_retrieval", "web_search"]
- `query`: The argument for the chosen tool. For `deep_graph_retrieval`, this is the original sub-query. For the others, it is the generated keyword or search phrase.

Example for `deep_graph_retrieval`:
{{"tool_to_use": "deep_graph_retrieval", "query": "What are the live load requirements in Section 1607.12?"}}

Example for `keyword_retrieval`:
{{"tool_to_use": "keyword_retrieval", "query": "ASTM E119"}}

Example for `web_search`:
{{"tool_to_use": "web_search", "query": "latest ACI 318 standards for concrete shear walls"}}

**JSON Response:**
"""

class ParallelResearchTool(BaseTool):
    """
    A tool that executes a research plan in parallel. For each sub-query, it uses the
    RetrievalStrategyAgent to determine the best way to find information, executes
    the single best retrieval method, and then generates a focused sub-answer.
    """

    def __init__(self):
        """Initializes the tool and the strategy agent it depends on."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.strategy_agent = RetrievalStrategyAgent()
        self.neo4j_connector = Neo4jConnector()

    @property
    def name(self) -> str:
        return "execute_parallel_research"

    @property
    def description(self) -> str:
        return (
            "Takes a research plan and executes it by determining the best retrieval strategy for each sub-query."
            "Input: {'plan': [{'sub_query': '...', 'hyde_document': '...'}], 'original_query': '...'}"
        )

    def _get_embedding(self, text: str) -> List[float]:
        """Generates an embedding for a given text."""
        response = genai.embed_content(
            model=EMBEDDING_MODEL, content=text, task_type="RETRIEVAL_DOCUMENT"
        )
        return response['embedding']

    async def _process_one_sub_query(self, sub_query_plan: Dict[str, str], original_query: str) -> Dict[str, Any]:
        """
        Processes a single sub-query by first determining the best retrieval strategy
        and then executing it.
        """
        sub_query = sub_query_plan.get('sub_query') or sub_query_plan.get('query')
        self.logger.info(f"--- Processing sub-query: '{sub_query[:80]}...' ---")
        start_time = time.time()

        # 1. Get the retrieval strategy from the specialized agent
        strategy_state = await self.strategy_agent.execute({"current_sub_query": sub_query})
        strategy = strategy_state.get("strategy", {})
        tool_to_use = strategy.get("tool", "vector_search")
        query_for_tool = strategy.get("query", sub_query)

        self.logger.info(f"Retrieval strategy selected: '{tool_to_use}' with query: '{query_for_tool}'")

        # 2. Execute the chosen retrieval strategy
        context_blocks = []
        if tool_to_use == "direct_subsection_lookup":
            # This tool returns a list with a single, comprehensive block
            context_blocks = self.neo4j_connector.get_full_subsection_context_by_id(query_for_tool)
        elif tool_to_use == "keyword_retrieval":
            # This tool returns a list of individual context blocks
            context_blocks = self.neo4j_connector.keyword_search(query_for_tool)
        else: # Default to vector_search
            embedding = self._get_embedding(sub_query_plan['hyde_document'])
            # Vector search also returns a list of context blocks
            context_blocks = self.neo4j_connector.vector_search(embedding, top_k=3)

        # 3. Generate the sub-answer from the retrieved context
        context_str = self._format_context_for_prompt(context_blocks)
        sub_answer = await self._generate_sub_answer(original_query, sub_query, context_str)

        duration = time.time() - start_time
        self.logger.info(f"--- Finished sub-query in {duration:.2f}s ---")

        return {
            'sub_query': sub_query,
            'answer': sub_answer,
            'retrieval_method': tool_to_use,
            'processing_time': duration
        }

    async def _generate_sub_answer(self, original_query: str, sub_query: str, context_str: str) -> str:
        """Generates a focused answer for a single sub-query using an LLM."""
        if not context_str or not context_str.strip() or context_str == "No valid context was formatted.":
            return "No information was found in the knowledge base for this sub-query."

        model = genai.GenerativeModel(TIER_2_MODEL_NAME)
        prompt = SUB_ANSWER_PROMPT.format(
            user_query=original_query,
            sub_query=sub_query,
            context_blocks=context_str
        )
        response = await model.generate_content_async(prompt)
        return response.text.strip()

    def _format_context_for_prompt(self, context_blocks: List[Dict]) -> str:
        """
        Formats the list of context dictionaries into a single string for the prompt.
        This function is designed to handle the nested structures from graph retrieval.
        """
        if not context_blocks:
            return ""

        formatted_string = ""
        for i, block in enumerate(context_blocks):
            primary_item = block.get('primary_item', {})
            supplemental_context = block.get('supplemental_context', {})

            parent_info = block if 'title' in block else primary_item
            if not parent_info: continue

            title = parent_info.get('title', 'No Title')
            number = parent_info.get('number', '')
            header = f"[{number} - {title}]"
            source_text = parent_info.get('text', '')

            formatted_string += f"Source {i+1}: {header}\n"
            if source_text and source_text.strip():
                formatted_string += f"Text: {source_text}\n"

            passages = supplemental_context.get("passages", [])
            if passages:
                passage_strings = [f"  - {item.get('title', 'Passage')}: {item.get('text', 'N/A')}" for item in passages]
                formatted_string += "Referenced Passages:\n" + "\n".join(passage_strings) + "\n"

            tables = supplemental_context.get("tables", [])
            if tables:
                table_strings = []
                for item in tables:
                    table_json = {'headers': item.get('headers', []), 'rows': item.get('rows', [])}
                    markdown_table = self._format_json_table_to_markdown(table_json)
                    table_strings.append(f"  - Table: {item.get('title', 'N/A')}\n{markdown_table}")
                formatted_string += "Tables:\n" + "\n".join(table_strings) + "\n"

            formatted_string += "\n"

        return formatted_string if formatted_string.strip() else "No valid context was formatted."

    def _format_json_table_to_markdown(self, table_data: Dict) -> str:
        """Formats a JSON table into a Markdown table string."""
        if not table_data or 'headers' not in table_data or 'rows' not in table_data:
            return " (Table data is malformed or empty)"
        headers = table_data['headers']
        rows = table_data['rows']
        header_line = " | ".join(headers)
        divider_line = " | ".join(['---'] * len(headers))
        row_lines = [" | ".join(str(item.get(h, '')) for h in headers) for item in rows]
        return "\n".join([header_line, divider_line] + row_lines)

    async def _run_async_logic(self, plan: List[Dict[str, str]], original_query: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Processes the sub-queries in the research plan in parallel.
        """
        self.logger.info(f"Executing research for {len(plan)} sub-queries.")
        tasks = [self._process_one_sub_query(p, original_query) for p in plan]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        processed_answers = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                sq = plan[i].get('sub_query') or plan[i].get('query', 'Unknown query')
                self.logger.error(f"An exception occurred while processing sub-query '{sq}': {result}", exc_info=True)
                processed_answers.append({"sub_query": sq, "answer": f"An unexpected error occurred: {result}"})
            else:
                processed_answers.append(result)

        self.logger.info(f"Research completed: {len(processed_answers)} sub-answers generated")
        return {"sub_answers": processed_answers}

    def __call__(self, plan: List[Dict[str, str]], original_query: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        The main synchronous entry point for the tool.
        """
        # This is now the sole responsibility of the execute method in the agent
        pass 