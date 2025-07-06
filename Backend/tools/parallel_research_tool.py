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
    A tool that executes a research plan in parallel. For each sub-query, it retrieves
    context and then uses an LLM to generate a focused "sub-answer".
    """

    @property
    def name(self) -> str:
        return "execute_parallel_research"

    @property
    def description(self) -> str:
        return (
            "Takes a research plan and executes it in parallel. For each sub-query, "
            "it retrieves relevant documents and synthesizes a focused 'sub-answer'. "
            "Use this after creating a plan."
            "Input: {'plan': [{'sub_query': '...', 'hyde_document': '...'}], 'original_query': '...'}"
        )

    def _get_embedding(self, text: str) -> List[float]:
        """Generates an embedding for a given text."""
        # Note: This might be better as a shared utility if other tools need it.
        response = genai.embed_content(
            model=EMBEDDING_MODEL, content=text, task_type="RETRIEVAL_DOCUMENT"
        )
        return response['embedding']

    async def _rerank_documents(self, reranker, sub_query, primary_items):
        """Helper to run async reranking."""
        docs_to_rerank = [{"text": str(item['text']), "uid": item['uid']} for item in primary_items if item.get('text')]
        return await reranker.rerank(query=sub_query, documents=docs_to_rerank, top_n=3)

    def _format_context_for_prompt(self, context_blocks: List[Dict[str, Any]]) -> str:
        """
        Formats a list of context blocks into a single string for the prompt.
        This function is designed to handle both standard retrieval results and the
        more complex nested structures from the deep graph fallback.
        """
        formatted_string = ""
        for i, block in enumerate(context_blocks):
            # The new hybrid search returns a deeply nested structure.
            # We need to robustly parse it.
            primary_item = block.get('primary_item', {})
            # Some retrieval functions return the extra context under the key
            # 'supplemental_context' (newer) while older fallback logic may use
            # 'supplementary_content'. Support both for robustness.
            supplemental_context = block.get('supplemental_context', {})
            if not supplemental_context and 'supplementary_content' in block:
                supplemental_context = block.get('supplementary_content', {})

            # The main parent info might be in the block itself or in the primary_item
            parent_info = block if 'title' in block else primary_item
            if not parent_info: continue

            title = parent_info.get('title', 'No Title')
            number = parent_info.get('number', '')
            header = f"[{number} - {title}]"
            source_text = parent_info.get('text', '')
            
            formatted_string += f"Source {i+1}: {header}\n"
            if source_text and source_text.strip():
                formatted_string += f"Text: {source_text}\n"

            # Combine children from all possible locations to be safe
            all_children = block.get('children', []) + supplemental_context.get('children', [])
            
            # The supplemental_context itself contains categorized children
            content_map = {
                "passages": supplemental_context.get("passages", []),
                "tables": supplemental_context.get("tables", []),
                "mathematical_content": supplemental_context.get("mathematical_content", []),
                "diagrams": supplemental_context.get("diagrams", [])
            }

            # If the main `all_children` list has items, categorize them as well.
            # This makes the function robust to different input structures.
            for child in all_children:
                if not isinstance(child, dict): continue
                node_type = child.get('type', 'Unknown').lower()
                if 'passage' in node_type or 'subsection' in node_type or 'section' in node_type:
                    content_map["passages"].append(child)
                elif 'table' in node_type:
                    content_map["tables"].append(child)
                elif 'math' in node_type:
                    content_map["mathematical_content"].append(child)
                elif 'diagram' in node_type:
                    content_map["diagrams"].append(child)

            if content_map["passages"]:
                # Avoid duplicates
                seen_passages = set()
                passage_strings = []
                for item in sorted(content_map["passages"], key=lambda x: str(x.get('number') or x.get('uid', ''))):
                    uid = item.get('uid')
                    if uid in seen_passages: continue
                    seen_passages.add(uid)
                    item_title = item.get('title', item.get('uid', 'N/A'))
                    item_text = item.get('text', 'N/A')
                    passage_strings.append(f"  - {item_title}: {item_text}")
                if passage_strings:
                    formatted_string += "Referenced Passages/Sections:\n"
                    formatted_string += "\n".join(passage_strings) + "\n"


            if content_map["mathematical_content"]:
                # Avoid duplicates
                seen_math = set()
                math_strings = []
                for item in content_map["mathematical_content"]:
                    uid = item.get('uid')
                    if uid in seen_math: continue
                    seen_math.add(uid)
                    math_strings.append(f"  - Formula ({item.get('uid', 'N/A')}): {item.get('latex', 'N/A')}")
                if math_strings:
                    formatted_string += "Mathematical Formulas:\n"
                    formatted_string += "\n".join(math_strings) + "\n"
            
            if content_map["tables"]:
                # Avoid duplicates
                seen_tables = set()
                table_strings = []
                for item in content_map["tables"]:
                    uid = item.get('uid')
                    if uid in seen_tables: continue
                    seen_tables.add(uid)
                    item_title = item.get('title', 'N/A')
                    
                    # The table data is now directly in the table node properties
                    table_json = {
                        'headers': item.get('headers', []),
                        'rows': item.get('rows', []),
                        'title': item.get('title', ''),
                        'table_id': item.get('table_id', 'Table')
                    }
                    
                    # Enhanced footnote support - detect footnote markers and extract explanations
                    footnote_markers = self._detect_footnote_markers_in_table(table_json) if table_json.get('headers') else []
                    footnote_explanations = {}
                    if footnote_markers:
                        footnote_explanations = self._extract_footnote_explanations_from_context(context_blocks, footnote_markers)
                    
                    # Use enhanced table formatter with footnote support
                    markdown_table = self._format_json_table_to_markdown(table_json, footnote_explanations)
                    table_strings.append(f"  - Table Title: {item_title}\n    Table Content:\n{markdown_table}")
                if table_strings:
                    formatted_string += "Tables:\n"
                    formatted_string += "\n".join(table_strings) + "\n"

            if content_map["diagrams"]:
                 # Avoid duplicates
                seen_diagrams = set()
                diagram_strings = []
                for item in content_map["diagrams"]:
                    uid = item.get('uid')
                    if uid in seen_diagrams: continue
                    seen_diagrams.add(uid)
                    item_path = item.get('path', 'N/A')
                    item_desc = item.get('text', 'N/A')
                    diagram_strings.append(f"  - Diagram Path: {item_path}\n  - Diagram Description: {item_desc}")
                if diagram_strings:
                    formatted_string += "Diagrams:\n"
                    formatted_string += "\n".join(diagram_strings) + "\n"

            formatted_string += "\n"
        # Return the final string, ensuring it's not just whitespace
        return formatted_string if formatted_string.strip() else "No valid context was formatted."

    def _format_json_table_to_markdown(self, table_data: Dict[str, Any], footnote_explanations: Dict[str, str] = None) -> str:
        """
        Enhanced table formatter with footnote support and hierarchical cell formatting.
        
        Args:
            table_data: JSON table structure with headers and rows
            footnote_explanations: Dictionary mapping footnote markers to their explanations
        
        Returns:
            Formatted table string with enhanced layout and footnotes
        """
        if not table_data or 'headers' not in table_data or 'rows' not in table_data:
            return " (Table data is malformed or empty)"

        headers = table_data['headers']
        rows = table_data['rows']
        table_title = table_data.get('title', '')
        table_id = table_data.get('table_id', 'Table')
        
        # Detect footnote markers in the table
        footnote_markers_found = set()
        footnote_pattern = r':([a-z])'
        
        # Build rows with enhanced hierarchical formatting
        formatted_rows = []
        for row_idx, row in enumerate(rows):
            formatted_row_values = []
            
            for header in headers:
                cell_values = row.get(header, [])
                if not isinstance(cell_values, list):
                    cell_values = [str(cell_values)] if cell_values else []
                
                # Check for footnote markers in this cell
                cell_footnote_marker = None
                for value in cell_values:
                    markers = re.findall(footnote_pattern, str(value).lower())
                    if markers:
                        cell_footnote_marker = markers[0]
                        footnote_markers_found.update(markers)
                        break
                
                # Format the cell hierarchically
                formatted_cell = self._format_hierarchical_cell(cell_values, cell_footnote_marker)
                formatted_row_values.append(formatted_cell)
            
            formatted_rows.append(formatted_row_values)
        
        # Build the complete table output
        table_header = f"{table_id}" + (f": {table_title}" if table_title and table_title.strip() else "")
        
        result = []
        result.append("=" * 80)
        result.append(f"{table_header}")
        result.append("=" * 80)
        result.append("")
        
        # Add headers
        result.append(" | ".join(headers))
        result.append(" | ".join(['---'] * len(headers)))
        
        # Add rows (handling multi-line cells properly)
        for row_values in formatted_rows:
            # Split multi-line cells and pad to same height
            cell_lines = []
            max_lines = 1
            
            for cell in row_values:
                lines = cell.split('\n') if cell else ['']
                cell_lines.append(lines)
                max_lines = max(max_lines, len(lines))
            
            # Pad cells to same height
            for cell_line_list in cell_lines:
                while len(cell_line_list) < max_lines:
                    cell_line_list.append('')
            
            # Output each line of the row
            for line_idx in range(max_lines):
                row_line = " | ".join(cell_lines[col_idx][line_idx] for col_idx in range(len(headers)))
                result.append(row_line)
        
        # Add footnotes if any were found
        if footnote_markers_found and footnote_explanations:
            result.append("")
            result.append("**FOOTNOTES:**")
            for marker in sorted(footnote_markers_found):
                if marker in footnote_explanations:
                    result.append(f"{marker}. {footnote_explanations[marker]}")
        
        return "\n".join(result)
    
    def _format_hierarchical_cell(self, cell_values: List[str], footnote_marker: str = None) -> str:
        """Format a cell with multiple values hierarchically."""
        if not cell_values:
            return "—"
        
        # If single value, return as is
        if len(cell_values) == 1:
            value = cell_values[0]
            if footnote_marker:
                value = value.replace(f":{footnote_marker}", f"ᶠⁿ{footnote_marker}")  # Mark footnote
            return value
        
        # Multiple values - format hierarchically
        primary = cell_values[0]
        if footnote_marker:
            primary = primary.replace(f":{footnote_marker}", f"ᶠⁿ{footnote_marker}")  # Mark footnote
        
        # Sub-items with indentation (using spaces for markdown compatibility)
        sub_items = []
        for item in cell_values[1:]:
            if item.strip() and item.strip() != "—":
                sub_items.append(f"  • {item}")
        
        if sub_items:
            return f"{primary}\n" + "\n".join(sub_items)
        else:
            return primary
    
    def _detect_footnote_markers_in_table(self, table_data: Dict) -> List[str]:
        """Extract all footnote markers from table headers and cells."""
        markers = set()
        footnote_pattern = r':([a-z])'
        
        # Check headers
        for header in table_data.get('headers', []):
            if isinstance(header, str):
                matches = re.findall(footnote_pattern, header.lower())
                markers.update(matches)
        
        # Check all cell values in all rows
        for row in table_data.get('rows', []):
            if isinstance(row, dict):
                for cell_key, cell_values in row.items():
                    if isinstance(cell_values, list):
                        for value in cell_values:
                            if isinstance(value, str):
                                matches = re.findall(footnote_pattern, value.lower())
                                markers.update(matches)
                    elif isinstance(cell_values, str):
                        matches = re.findall(footnote_pattern, cell_values.lower())
                        markers.update(matches)
            elif isinstance(row, list):
                # Handle case where row is a list of values
                for cell_value in row:
                    if isinstance(cell_value, str):
                        matches = re.findall(footnote_pattern, cell_value.lower())
                        markers.update(matches)
            elif isinstance(row, str):
                # Handle case where row is a string
                matches = re.findall(footnote_pattern, row.lower())
                markers.update(matches)
        
        return sorted(list(markers))
    
    def _extract_footnote_explanations_from_context(self, context_blocks: List[Dict[str, Any]], markers: List[str]) -> Dict[str, str]:
        """Extract footnote explanations from context blocks."""
        explanations = {}
        
        # Look through all context blocks for footnote explanations
        for block in context_blocks:
            # Check primary item content
            primary_item = block.get('primary_item', {})
            if primary_item and isinstance(primary_item.get('text'), str):
                content_lines = primary_item['text'].split('\n')
                explanations.update(self._extract_footnote_explanations_from_content(content_lines, markers))
            
            # Also check if there are any content arrays in the block structure
            if hasattr(block, 'get') and 'content' in block:
                content = block['content']
                if isinstance(content, list):
                    explanations.update(self._extract_footnote_explanations_from_content(content, markers))
        
        return explanations
    
    def _extract_footnote_explanations_from_content(self, content: List[str], markers: List[str]) -> Dict[str, str]:
        """Extract footnote explanations from content lines."""
        explanations = {}
        
        for line in content:
            if isinstance(line, str):
                for marker in markers:
                    # Look for "a. explanation text" patterns
                    pattern = f"^{marker}\\. (.+)"
                    match = re.match(pattern, line.strip())
                    if match:
                        explanations[marker] = match.group(1)
        
        return explanations

    def _generate_sub_answer(self, original_query: str, sub_query: str, context_str: str) -> str:
        """Generates a focused answer for a single sub-query."""
        logging.info(f"Generating sub-answer for: '{sub_query[:50]}...'")
        model = genai.GenerativeModel(TIER_2_MODEL_NAME) # Use a faster model for sub-tasks
        prompt = SUB_ANSWER_PROMPT.format(
            user_query=original_query,
            sub_query=sub_query,
            context_blocks=context_str
        )
        response = model.generate_content(prompt)
        return response.text.strip()

    def _is_context_sufficient(self, sub_query: str, context_str: str) -> bool:
        """Uses an LLM to check if the retrieved context is sufficient to answer the sub-query."""
        if not context_str or not context_str.strip():
            return False
            
        logging.info(f"Checking context quality for sub-query: '{sub_query[:50]}...'")
        model = genai.GenerativeModel(TIER_2_MODEL_NAME)
        prompt = QUALITY_CHECK_PROMPT.format(sub_query=sub_query, context_str=context_str)
        
        try:
            response = model.generate_content(prompt)
            classification = response.text.strip().lower()
            logging.info(f"Context quality classification: '{classification}'")
            return classification == "sufficient"
        except Exception as e:
            logging.error(f"Error during context quality check: {e}")
            return False # Assume insufficient on error

    def _extract_subsections_from_context(self, sub_query: str, context_str: str) -> List[str]:
        """
        Ask LLM to analyze partial context and suggest which subsections 
        likely contain the missing table/equation/diagram.
        
        Args:
            sub_query: The sub-query that needs more context
            context_str: The insufficient context retrieved so far
            
        Returns:
            List of subsection numbers (e.g., ['1607.12.1', '1604.3'])
        """
        logging.info(f"Extracting subsection suggestions for: '{sub_query[:50]}...'")
        model = genai.GenerativeModel(TIER_2_MODEL_NAME)
        prompt = SUBSECTION_EXTRACTION_PROMPT.format(
            sub_query=sub_query, 
            context_str=context_str
        )
        
        try:
            response = model.generate_content(prompt)
            suggestions = response.text.strip()
            
            if suggestions.upper() == "NONE":
                logging.info("No subsection suggestions found")
                return []
            
            # Parse comma-separated subsection numbers
            subsections = [s.strip() for s in suggestions.split(',') if s.strip()]
            
            # Validate format (basic regex check for subsection patterns)
            valid_subsections = []
            subsection_pattern = r'^\d{4}(\.\d+)*$'
            
            for subsection in subsections:
                # Add a check to ensure the subsection is a string
                if not isinstance(subsection, str):
                    logging.warning(f"Invalid subsection format suggested (not a string): {subsection}")
                    continue

                if re.match(subsection_pattern, subsection):
                    valid_subsections.append(subsection)
                else:
                    logging.warning(f"Invalid subsection format suggested: '{subsection}'")
            
            logging.info(f"Extracted valid subsection suggestions: {valid_subsections}")
            return valid_subsections
            
        except Exception as e:
            logging.error(f"Error extracting subsections: {e}")
            return []

    def _is_context_sufficient_with_extraction(self, sub_query: str, context_str: str) -> tuple[bool, List[str]]:
        """
        Enhanced context quality check that also suggests subsections to retrieve
        if context is insufficient.
        
        Args:
            sub_query: The sub-query to evaluate
            context_str: The context to evaluate
            
        Returns:
            Tuple of (is_sufficient, suggested_subsections_to_retrieve)
        """
        # First, check if context is already sufficient
        if self._is_context_sufficient(sub_query, context_str):
            return True, []
        
        # If insufficient, ask LLM to suggest subsections that might help
        suggested_subsections = self._extract_subsections_from_context(sub_query, context_str)
        return False, suggested_subsections

    def _extract_subsection_from_table_reference(self, query: str) -> str:
        """
        Extract subsection number from table references like "Table 1607.12.1"
        Returns the subsection number or None if no table reference is found.
        """
        # Pattern to match table references like "Table 1607.12.1" or "Table 1607.1"
        table_pattern = r'Table\s+(\d+(?:\.\d+)+)'
        match = re.search(table_pattern, query, re.IGNORECASE)
        
        if match:
            return match.group(1)
            return None

    # === PHASE 2: NEW EQUATION HANDLING LOGIC ===
    
    def _contains_equation_reference(self, query: str) -> bool:
        """
        Check if the query contains a reference to a specific equation.
        """
        equation_patterns = [
            r'Equation\s+\d+-\d+',
            r'Equation\s+\(\d+-\d+\)',
            r'equation\s+\d+-\d+',
            r'Eq\.\s+\d+-\d+'
        ]
        
        for pattern in equation_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        return False
    
    def _is_standard_building_code_query(self, query: str) -> bool:
        """
        Detect standard building code queries that should use optimized retrieval
        to avoid unnecessary fallbacks to web search.
        """
        # Common building code query patterns
        standard_patterns = [
            r'live load requirements?',
            r'wind load requirements?',
            r'seismic requirements?',
            r'dead load requirements?',
            r'load combinations?',
            r'deflection limits?',
            r'allowable stress',
            r'design loads?',
            r'structural requirements?',
            r'building code requirements?',
            r'what are the.*requirements?.*(?:section|chapter)',
            r'requirements?.*(?:section|chapter).*\d+',
            r'provisions?.*(?:section|chapter)',
            r'according to.*section',
        ]
        
        query_lower = query.lower()
        for pattern in standard_patterns:
            if re.search(pattern, query_lower):
                return True
        return False
    
    def _extract_section_reference(self, query: str) -> str:
        """
        Extract section number from queries like "According to Section 1607.12.1" 
        or "What are the requirements in Section 1604.3?"
        """
        section_patterns = [
            r'section\s+(\d+(?:\.\d+)*)',
            r'chapter\s+(\d+)',
            r'(\d{4}\.\d+(?:\.\d+)*)',  # Direct section numbers like 1607.12.1
        ]
        
        for pattern in section_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _extract_equation_reference(self, query: str) -> tuple[str, str]:
        """
        Extract equation reference from query.
        Returns (chapter_num, equation_num) or (None, None) if not found.
        """
        equation_patterns = [
            r'Equation\s+(\d+)-(\d+)',
            r'Equation\s+\((\d+)-(\d+)\)',
            r'equation\s+(\d+)-(\d+)',
            r'Eq\.\s+(\d+)-(\d+)'
        ]
        
        for pattern in equation_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1), match.group(2)
        
        return None, None
    
    def _get_all_chapter_nodes(self, chapter_num: str) -> list:
        """
        Get all nodes in a specific chapter.
        """
        try:
            # Query to find all nodes in a chapter
            # For Chapter 16, we need nodes starting with "160", "161", etc.
            query = """
            MATCH (n)
            WHERE n.uid STARTS WITH $chapter_prefix
            RETURN n.uid AS uid, n.text AS text, n.latex AS latex, labels(n) AS labels
            """
            
            # For Chapter 16, search for UIDs starting with "160"
            chapter_prefix = f"{chapter_num}0"
            parameters = {"chapter_prefix": chapter_prefix}
            
            records = Neo4jConnector.execute_query(query, parameters)
            return [record.data() for record in records]
            
        except Exception as e:
            logging.error(f"Error getting chapter {chapter_num} nodes: {e}")
            return []
    
    def _find_exact_equation_matches(self, chapter_nodes: list, exact_text: str) -> list:
        """
        Find nodes containing exact equation text match.
        Filters out reference nodes (containing "refer", "see", etc.).
        """
        matching_nodes = []
        
        for node in chapter_nodes:
            node_text = node.get('text', '') or ''
            node_latex = node.get('latex', '') or ''
            
            # Check for exact match in text or latex
            if exact_text in node_text or exact_text in node_latex:
                # Filter out reference nodes
                text_lower = node_text.lower()
                if not any(ref_word in text_lower for ref_word in ['refer', 'see', 'according to', 'as per']):
                    matching_nodes.append(node)
        
        return matching_nodes
    
    def _filter_actual_equation_nodes(self, nodes: list) -> list:
        """
        Filter for actual equation nodes vs. reference nodes.
        Prioritize Math nodes and nodes with latex content.
        """
        actual_equation_nodes = []
        
        for node in nodes:
            labels = node.get('labels', [])
            latex = node.get('latex', '')
            
            # Prioritize Math nodes or nodes with latex content
            if 'Math' in labels or latex:
                actual_equation_nodes.append(node)
            # Also include other nodes that might contain the equation
            elif node.get('text', ''):
                actual_equation_nodes.append(node)
        
        return actual_equation_nodes
    
    def _get_connected_subsection_content(self, equation_node: dict) -> list:
        """
        Get all content connected to the subsection containing the equation.
        """
        try:
            equation_uid = equation_node.get('uid')
            if not equation_uid:
                return []
            
            # Find the parent subsection and get all its content
            expanded_context = Neo4jConnector.get_gold_standard_context(equation_uid)
            if expanded_context:
                return [{
                    'primary_item': expanded_context.get('primary_item', {}),
                    'supplemental_context': expanded_context.get('supplemental_context', {}),
                    'children': expanded_context.get('children', []),
                    'expansion_type': 'equation_subsection_context'
                }]
            
                return []
            
        except Exception as e:
            logging.error(f"Error getting connected subsection content: {e}")
            return []
    
    def _get_all_math_nodes_in_chapter(self, chapter_num: str) -> list:
        """
        Get all Math nodes in a specific chapter for LLM selection.
        """
        try:
            query = """
            MATCH (n:Math)
            WHERE n.uid STARTS WITH $chapter_prefix
            RETURN n.uid AS uid, n.text AS text, n.latex AS latex, n.number AS number
            ORDER BY n.uid
            """
            
            # For Chapter 16, search for Math nodes starting with "160"
            chapter_prefix = f"{chapter_num}0"
            parameters = {"chapter_prefix": chapter_prefix}
            
            records = Neo4jConnector.execute_query(query, parameters)
            return [record.data() for record in records]
            
        except Exception as e:
            logging.error(f"Error getting math nodes in chapter {chapter_num}: {e}")
            return []
    
    def _handle_equation_query(self, query: str) -> tuple[str, bool, list]:
        """
        Handle equation queries by finding reference nodes and their connected math nodes.
        
        Returns:
            tuple: (modified_query, was_handled, context_blocks)
        """
        try:
            # Extract equation reference
            chapter_num, equation_num = self._extract_equation_reference(query)
            if not chapter_num or not equation_num:
                return query, False, []
            
            exact_text = f"Equation {chapter_num}-{equation_num}"
            logging.info(f"Handling equation query for: {exact_text}")
            
            # NEW APPROACH: Find reference nodes, then get their subsection's math nodes
            reference_query = """
            MATCH (ref_node)
            WHERE ref_node.text CONTAINS $equation_text
            RETURN ref_node.uid AS ref_uid, ref_node.text AS ref_text, labels(ref_node) AS labels
            """
            
            ref_results = Neo4jConnector.execute_query(reference_query, {"equation_text": exact_text})
            if not ref_results:
                logging.warning(f"No reference nodes found for {exact_text}")
                return query, False, []
            
            logging.info(f"Found {len(ref_results)} reference nodes for {exact_text}")
            
            # Get the subsection UIDs from reference nodes
            subsection_uids = set()
            for ref_result in ref_results:
                ref_uid = ref_result['ref_uid']
                # Extract subsection UID (e.g., "1607.12.1" from "1607.12.1-passage-0")
                if '-' in ref_uid:
                    subsection_uid = ref_uid.split('-')[0]
                    subsection_uids.add(subsection_uid)
                    logging.info(f"Found reference in subsection: {subsection_uid}")
            
            if not subsection_uids:
                logging.warning("Could not extract subsection UIDs from reference nodes")
                return query, False, []
            
            # For each subsection, get all its Math nodes directly
            context_blocks = []
            for subsection_uid in subsection_uids:
                try:
                    # Use direct query to get subsection and its Math nodes
                    direct_query = """
                    MATCH (subsection {uid: $subsection_uid})
                    OPTIONAL MATCH (subsection)-[:CONTAINS]->(math:Math)
                    OPTIONAL MATCH (subsection)-[:HAS_CHUNK]->(passage:Passage)
                    OPTIONAL MATCH (subsection)-[:CONTAINS]->(table:Table)
                    RETURN subsection,
                           COLLECT(DISTINCT math) AS math_nodes,
                           COLLECT(DISTINCT passage) AS passage_nodes,
                           COLLECT(DISTINCT table) AS table_nodes
                    """
                    
                    results = Neo4jConnector.execute_query(direct_query, {"subsection_uid": subsection_uid})
                    if results:
                        record = results[0]
                        subsection_node = record['subsection']
                        math_nodes = [node for node in record['math_nodes'] if node is not None]
                        passage_nodes = [node for node in record['passage_nodes'] if node is not None]
                        table_nodes = [node for node in record['table_nodes'] if node is not None]
                        
                        logging.info(f"Direct query for {subsection_uid}: {len(math_nodes)} math, {len(passage_nodes)} passages, {len(table_nodes)} tables")
                        
                        # Format subsection data
                        primary_item = {
                            'uid': subsection_node.get('uid'),
                            'title': subsection_node.get('title'),
                            'text': subsection_node.get('text', ''),
                            'number': subsection_node.get('number'),
                            'type': 'Subsection'
                        }
                        
                        # Format children
                        children = []
                        
                        # Add math nodes
                        for math_node in math_nodes:
                            math_data = {
                                'uid': math_node.get('uid'),
                                'text': math_node.get('text'),
                                'latex': math_node.get('latex'),
                                'type': 'Math'
                            }
                            children.append(math_data)
                            latex = math_node.get('latex', '')
                            if 'L=' in latex or 'L =' in latex:
                                logging.info(f"Found equation formula in Math node {math_node.get('uid')}: {latex}")
                        
                        # Add passage nodes
                        for passage_node in passage_nodes:
                            passage_data = {
                                'uid': passage_node.get('uid'),
                                'text': passage_node.get('text'),
                                'type': 'Passage'
                            }
                            children.append(passage_data)
                        
                        # Add table nodes
                        for table_node in table_nodes:
                            # Parse JSON strings for headers and rows if needed
                            import json
                            try:
                                headers = table_node.get('headers', [])
                                if isinstance(headers, str):
                                    headers = json.loads(headers)
                                
                                rows = table_node.get('rows', [])
                                if isinstance(rows, str):
                                    rows = json.loads(rows)
                                    
                            except json.JSONDecodeError:
                                # If JSON parsing fails, use empty defaults
                                headers = []
                                rows = []
                            
                            table_data = {
                                'uid': table_node.get('uid'),
                                'text': table_node.get('text'),
                                'title': table_node.get('title', ''),
                                'table_id': table_node.get('table_id', 'Table'),
                                'headers': headers,
                                'rows': rows,
                                'type': 'Table'
                            }
                            children.append(table_data)
                        
                        # Create context block
                        context_block = {
                            'primary_item': primary_item,
                            'supplemental_context': {},
                            'children': children,
                            'expansion_type': 'equation_direct_subsection_query'
                        }
                        context_blocks.append(context_block)
                        logging.info(f"Successfully created context block for {subsection_uid} with {len(children)} children")
                        
                except Exception as e:
                    logging.warning(f"Error retrieving subsection {subsection_uid}: {e}")
                    continue
            
            if context_blocks:
                logging.info(f"Successfully retrieved {len(context_blocks)} context blocks with equation content")
                return query, True, context_blocks
            
            # Fallback - get all math nodes in chapter
            logging.info(f"No subsection context found, using math nodes fallback for chapter {chapter_num}")
            all_math_nodes = self._get_all_math_nodes_in_chapter(chapter_num)
            
            if all_math_nodes:
                # Create a context block with all math nodes for LLM selection
                fallback_context = {
                    'primary_item': {
                        'title': f'Chapter {chapter_num} Mathematical Content',
                        'text': f'All equations and mathematical content from Chapter {chapter_num}',
                        'uid': f'chapter_{chapter_num}_math'
                    },
                    'supplemental_context': {
                        'mathematical_content': all_math_nodes
                    },
                    'children': [],
                    'expansion_type': 'equation_chapter_fallback'
                }
                
                logging.info(f"Using fallback with {len(all_math_nodes)} math nodes from chapter {chapter_num}")
                return query, True, [fallback_context]
            
            return query, False, []
            
        except Exception as e:
            logging.error(f"Error handling equation query: {e}")
            return query, False, []

    # === END PHASE 2 EQUATION HANDLING ===

    def _get_subsection_with_all_nodes(self, subsection_number: str) -> List[Dict[str, Any]]:
        """
        Fetches a complete subsection with all its connected nodes (tables, math, diagrams, etc.).
        Returns it in the same format as vector search results for consistency.
        """
        try:
            # Use the enhanced gold standard context method
            result = Neo4jConnector.get_gold_standard_context(subsection_number)
            
            if not result:
                return []
            
            # Format as a single context block that matches the expected structure
            context_block = {
                'primary_item': {
                    'uid': result.get('uid'),
                    'title': result.get('title'),
                    'number': result.get('number'),
                    'text': result.get('text', ''),
                    'type': result.get('type', 'Subsection')
                },
                'supplemental_context': result.get('supplemental_context', {}),
                'children': result.get('children', [])
            }
            
            return [context_block]
            
        except Exception as e:
            logging.error(f"Error fetching subsection {subsection_number}: {e}")
            return []

    def _enhance_context_with_related_sections(self, sub_query: str, initial_context_blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        When initial context is insufficient, this method attempts to find related sections,
        tables, and formulas that might provide the missing information.
        """
        enhanced_blocks = initial_context_blocks.copy()
        
        # Extract section numbers from the sub-query
        import re
        section_pattern = r'(\d{4}\.\d{1,2}(?:\.\d{1,2})?)'
        sections_mentioned = re.findall(section_pattern, sub_query)
        
        for section in sections_mentioned:
            try:
                # Look for related sections (e.g., if 1607.12.1 fails, try 1607.12, 1607.12.2, etc.)
                base_section = '.'.join(section.split('.')[:2])  # Get 1607.12 from 1607.12.1
                
                # Try to get the broader section context
                broader_context = Neo4jConnector.get_full_subsection_context_by_id(base_section)
                if broader_context:
                    enhanced_blocks.append({
                        'primary_item': broader_context.get('primary_item', {}),
                        'supplemental_context': broader_context.get('supplemental_context', {}),
                        'children': broader_context.get('children', []),
                        'expansion_type': 'broader_section'
                    })
                
                # Look for sibling sections (1607.12.1, 1607.12.2, etc.)
                for suffix in ['1', '2', '3', '4', '5']:
                    sibling_section = f"{base_section}.{suffix}"
                    if sibling_section != section:  # Don't repeat the original
                        sibling_context = Neo4jConnector.get_gold_standard_context(sibling_section)
                        if sibling_context and sibling_context.get('primary_item'):
                            enhanced_blocks.append({
                                'primary_item': sibling_context.get('primary_item', {}),
                                'supplemental_context': sibling_context.get('supplemental_context', {}),
                                'children': sibling_context.get('children', []),
                                'expansion_type': 'sibling_section'
                            })
                            
            except Exception as e:
                logging.warning(f"Error expanding context for section {section}: {e}")
                continue
        
        # Look for specific table references if the query mentions tables or equations
        table_pattern = r'Table\s+(\d{4}\.\d{1,2}(?:\.\d{1,2})?)'
        equation_pattern = r'Equation\s+(\d{1,2}-\d{1,2})'
        
        tables_mentioned = re.findall(table_pattern, sub_query, re.IGNORECASE)
        equations_mentioned = re.findall(equation_pattern, sub_query, re.IGNORECASE)
        
        # Search for specific tables
        for table_ref in tables_mentioned:
            try:
                # Try to find the table by searching for nodes containing the table reference
                table_search_query = f"MATCH (n) WHERE n.text CONTAINS 'Table {table_ref}' OR n.title CONTAINS 'Table {table_ref}' RETURN n LIMIT 3"
                table_results = Neo4jConnector.execute_query(table_search_query)
                
                for result in table_results:
                    table_node = result['n']
                    table_context = Neo4jConnector.get_gold_standard_context(table_node.get('uid'))
                    if table_context:
                        enhanced_blocks.append({
                            'primary_item': table_context.get('primary_item', {}),
                            'supplemental_context': table_context.get('supplemental_context', {}),
                            'children': table_context.get('children', []),
                            'expansion_type': 'table_search'
                        })
            except Exception as e:
                logging.warning(f"Error searching for table {table_ref}: {e}")
                continue
        
        # Search for specific equations
        for equation_ref in equations_mentioned:
            try:
                # Search for equation references
                equation_search_query = f"MATCH (n) WHERE n.text CONTAINS 'Equation {equation_ref}' OR n.latex CONTAINS '{equation_ref}' RETURN n LIMIT 3"
                equation_results = Neo4jConnector.execute_query(equation_search_query)
                
                for result in equation_results:
                    eq_node = result['n']
                    eq_context = Neo4jConnector.get_gold_standard_context(eq_node.get('uid'))
                    if eq_context:
                        enhanced_blocks.append({
                            'primary_item': eq_context.get('primary_item', {}),
                            'supplemental_context': eq_context.get('supplemental_context', {}),
                            'children': eq_context.get('children', []),
                            'expansion_type': 'equation_search'
                        })
            except Exception as e:
                logging.warning(f"Error searching for equation {equation_ref}: {e}")
                continue
        
        logging.info(f"Enhanced context from {len(initial_context_blocks)} to {len(enhanced_blocks)} blocks")
        return enhanced_blocks

    async def _process_one_sub_query(self, sub_query_plan: Dict[str, str], original_query: str) -> Dict[str, Any]:
        """
        Processes a single sub-query through the sequential fallback mechanism:
        1. Vector Search + Deep Context Expansion (with Phase 2 enhancements)
        2. Keyword Search (if insufficient)
        3. Web Search (if still insufficient)
        """
        # Performance monitoring
        start_time = time.time()
        
        # Handle both old and new planning tool output formats
        sub_query = sub_query_plan.get('sub_query') or sub_query_plan.get('query')
        hyde_document = sub_query_plan['hyde_document']
        
        logging.info(f"--- Starting processing for sub-query: '{sub_query[:50]}...' ---")

        # Attempt 1: Vector Search with Gold Standard Context expansion
        logging.info("Attempt 1: Running Vector Search with Gold Standard Context expansion.")
        
        # PHASE 2: Enhanced query analysis and redirection
        context_blocks = []
        retrieval_method = 'vector_search'
        
        # Check for equation references first (Phase 2)
        if self._contains_equation_reference(sub_query):
            logging.info("Detected equation reference. Using Phase 2 equation handling.")
            modified_query, was_handled, equation_context = self._handle_equation_query(sub_query)
            
            if was_handled and equation_context:
                context_blocks = equation_context
                retrieval_method = 'phase2_equation_handling'
                logging.info(f"Phase 2 equation handling successful. Retrieved {len(context_blocks)} context blocks.")
            else:
                logging.warning("Phase 2 equation handling failed, falling back to standard vector search.")
        
        # Check for table references (existing logic)
        elif self._extract_subsection_from_table_reference(sub_query):
            subsection_number = self._extract_subsection_from_table_reference(sub_query)
            logging.info(f"Detected table reference. Using subsection-based retrieval for: {subsection_number}")
            context_blocks = self._get_subsection_with_all_nodes(subsection_number)
            retrieval_method = 'table_subsection_retrieval'
        
        # NEW: Check for standard building code queries and optimize retrieval
        elif self._is_standard_building_code_query(sub_query):
            logging.info("Detected standard building code query. Using optimized retrieval to avoid fallbacks.")
            section_ref = self._extract_section_reference(sub_query)
            
            if section_ref:
                logging.info(f"Found section reference: {section_ref}. Using direct subsection retrieval.")
                context_blocks = self._get_subsection_with_all_nodes(section_ref)
                retrieval_method = 'optimized_section_retrieval'
            else:
                logging.info("No specific section found. Using enhanced vector search with broader context.")
                # Use standard vector search but with enhanced context expansion
                embedding = self._get_embedding(hyde_document)
                primary_items = Neo4jConnector.comprehensive_vector_search(embedding, top_k=5)  # Get more results
                
                # Expand each primary result with gold standard context
                for item in primary_items:
                    uid = item['uid']
                    expanded_context = Neo4jConnector.get_gold_standard_context(uid)
                    if expanded_context:
                        context_blocks.append({
                            'primary_item': item,
                            'supplemental_context': expanded_context.get('supplemental_context', {}),
                            'children': expanded_context.get('children', [])
                        })
                
                # Immediately apply enhanced context expansion for standard queries
                context_blocks = self._enhance_context_with_related_sections(sub_query, context_blocks)
                retrieval_method = 'optimized_standard_query'
        
        # Standard vector search if no special handling was applied
        if not context_blocks:
            logging.info("Using standard vector search + context expansion.")
            embedding = self._get_embedding(hyde_document)
            primary_items = Neo4jConnector.comprehensive_vector_search(embedding, top_k=3)
            
            # Expand each primary result with gold standard context
            for item in primary_items:
                uid = item['uid']
                expanded_context = Neo4jConnector.get_gold_standard_context(uid)
                if expanded_context:
                    context_blocks.append({
                        'primary_item': item,
                        'supplemental_context': expanded_context.get('supplemental_context', {}),
                        'children': expanded_context.get('children', [])
                    })
        
        # PHASE 3: Apply quality enhancements to context blocks (safe)
        try:
            context_blocks = self._apply_phase3_quality_enhancements(sub_query, context_blocks)
        except Exception as e:
            logging.warning(f"Phase 3 quality enhancement failed, continuing with original context: {e}")
        
        # NEW: Context-aware table detection and retrieval
        try:
            context_blocks = self._detect_and_retrieve_missing_tables(context_blocks, sub_query)
        except Exception as e:
            logging.warning(f"Context-aware table detection failed, continuing: {e}")
        
        # Check if the context is sufficient with smart subsection extraction
        context_str = self._format_context_for_prompt(context_blocks)
        logging.info(f"Checking context quality for sub-query: '{sub_query[:50]}...'")
        
        is_sufficient, suggested_subsections = self._is_context_sufficient_with_extraction(sub_query, context_str)
        
        if is_sufficient:
            logging.info("Context quality classification: 'sufficient'")
            logging.info(f"Generating sub-answer for: '{sub_query[:50]}...'")
            sub_answer = self._generate_sub_answer(original_query, sub_query, context_str)
            
            # Performance monitoring
            end_time = time.time()
            duration = end_time - start_time
            logging.info(f"⏱️  Sub-query processing time: {duration:.2f} seconds")
            if duration > 4.0:
                logging.warning(f"🐌 PERFORMANCE WARNING: Query took {duration:.2f}s (>{4.0}s threshold)")
            
            logging.info(f"--- Finished processing for sub-query: '{sub_query}' ---")
            return {
                'sub_query': sub_query, 
                'answer': sub_answer,
                'retrieval_method': retrieval_method,
                'processing_time': duration
            }
        
        # NEW: Smart Subsection Enhancement - try suggested subsections before fallback
        elif suggested_subsections:
            logging.info(f"Context insufficient, but LLM suggested subsections: {suggested_subsections}")
            logging.info("Attempting smart subsection enhancement...")
            
            enhanced_context_blocks = context_blocks.copy()
            
            for subsection_num in suggested_subsections:
                try:
                    subsection_context = self._get_subsection_with_all_nodes(subsection_num)
                    enhanced_context_blocks.extend(subsection_context)
                    logging.info(f"Added subsection {subsection_num} to context")
                except Exception as e:
                    logging.warning(f"Could not retrieve subsection {subsection_num}: {e}")
            
            # Re-format and re-evaluate enhanced context
            enhanced_context_str = self._format_context_for_prompt(enhanced_context_blocks)
            
            if self._is_context_sufficient(sub_query, enhanced_context_str):
                logging.info("Smart subsection enhancement successful! Context now sufficient.")
                sub_answer = self._generate_sub_answer(original_query, sub_query, enhanced_context_str)
                logging.info(f"--- Finished processing for sub-query: '{sub_query}' ---")
                return {
                    'sub_query': sub_query, 
                    'answer': sub_answer,
                    'retrieval_method': 'smart_subsection_enhancement',
                    'enhanced_with_subsections': suggested_subsections
                }
            else:
                logging.info("Smart subsection enhancement insufficient, continuing to related sections expansion...")
                # Use the enhanced context as the starting point for further expansion
                context_blocks = enhanced_context_blocks
                context_str = enhanced_context_str
        
        # Attempt 1.5: Enhanced Context Expansion
        logging.info("Context quality classification: 'insufficient'")
        logging.info("Attempting enhanced context expansion with related sections and tables...")
        
        # CRITICAL FIX: Ensure enhanced_context_blocks is always defined
        try:
            enhanced_context_blocks = self._enhance_context_with_related_sections(sub_query, context_blocks)
            enhanced_context_str = self._format_context_for_prompt(enhanced_context_blocks)
        except Exception as e:
            logging.warning(f"Enhanced context expansion failed: {e}")
            enhanced_context_blocks = context_blocks.copy()  # Fallback
            enhanced_context_str = context_str
        
        logging.info(f"Checking enhanced context quality for sub-query: '{sub_query[:50]}...'")
        if self._is_context_sufficient(sub_query, enhanced_context_str):
            logging.info("Enhanced context quality classification: 'sufficient'")
            logging.info(f"Generating sub-answer with enhanced context for: '{sub_query[:50]}...'")
            sub_answer = self._generate_sub_answer(original_query, sub_query, enhanced_context_str)
            logging.info(f"--- Finished processing for sub-query: '{sub_query}' ---")
            return {
                'sub_query': sub_query, 
                'answer': sub_answer,
                'retrieval_method': f'{retrieval_method}_enhanced'
            }
        
        # Attempt 2: Keyword Search Fallback
        logging.info("Enhanced context quality classification: 'insufficient'")
        logging.warning("Enhanced context insufficient. Triggering Fallback 1: Keyword Search.")
        
        keyword_tool = KeywordRetrievalTool()
        keyword_results = keyword_tool(sub_query)
        
        # Format keyword results as context blocks (simplified)
        keyword_context_blocks = [{'primary_item': {'text': keyword_results, 'title': 'Keyword Search Results'}}]
        keyword_context_str = self._format_context_for_prompt(keyword_context_blocks)
        
        logging.info(f"Checking context quality for sub-query: '{sub_query[:50]}...'")
        if self._is_context_sufficient(sub_query, keyword_context_str):
            logging.info("Context quality classification: 'sufficient'")
            logging.info(f"Generating sub-answer for: '{sub_query[:50]}...'")
            sub_answer = self._generate_sub_answer(original_query, sub_query, keyword_context_str)
            logging.info(f"--- Finished processing for sub-query: '{sub_query}' ---")
            return {
                'sub_query': sub_query, 
                'answer': sub_answer,
                'retrieval_method': 'keyword_search_fallback'
            }
        
        # Attempt 3: Web Search Fallback with LLM Query Optimization
        logging.info("Context quality classification: 'insufficient'")
        logging.warning("Keyword context insufficient. Triggering Fallback 2: Web Search with Query Optimization.")
        
        # NEW: LLM-powered query optimization for Tavily
        optimized_web_query = await self._optimize_query_for_web_search(sub_query, original_query, context_str)
        
        web_tool = TavilySearchTool()
        web_results = web_tool(optimized_web_query)
        
        # Format web results as context blocks (simplified)
        web_context_blocks = [{'primary_item': {'text': web_results, 'title': 'Web Search Results'}}]
        web_context_str = self._format_context_for_prompt(web_context_blocks)
        
        # Generate final answer with web search results (no more fallbacks)
        logging.info(f"Generating sub-answer for: '{sub_query[:50]}...'")
        sub_answer = self._generate_sub_answer(original_query, sub_query, web_context_str)
        
        # Performance monitoring
        end_time = time.time()
        duration = end_time - start_time
        logging.info(f"⏱️  Sub-query processing time: {duration:.2f} seconds")
        if duration > 4.0:
            logging.warning(f"🐌 PERFORMANCE WARNING: Query took {duration:.2f}s (>{4.0}s threshold)")
        
        logging.info(f"--- Finished processing for sub-query: '{sub_query}' ---")
        return {
            'sub_query': sub_query, 
            'answer': sub_answer,
            'retrieval_method': 'web_search_fallback',
            'optimized_web_query': optimized_web_query,
            'processing_time': duration
        }

    async def _handle_insufficient_context(self, sub_query: str, original_query: str) -> Dict[str, Any]:
        """
        Handles cases where initial context is insufficient by re-planning.
        """
        self.logger.warning(f"Initial context for sub-query '{sub_query[:100]}...' was insufficient. Initiating re-planning.")
        
        prompt = RE_PLANNING_PROMPT.format(sub_query=sub_query, original_query=original_query)
        
        try:
            # Use a powerful model for this critical reasoning step
            model = genai.GenerativeModel(TIER_1_MODEL_NAME)
            response = await model.generate_content_async(prompt)
            response_text = response.text.strip()
            
            # More robust JSON parsing
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON object found in re-planning response.")
                
            re_plan_data = json.loads(json_match.group(0))

            tool_to_use = re_plan_data.get("tool_to_use")
            search_query = re_plan_data.get("search_query")
            
            self.logger.info(f"Re-planning decided to use '{tool_to_use}' with query: '{search_query}'")
            
            result = {}
            if tool_to_use == "keyword_retrieval":
                # Keyword tool returns a list of context blocks
                context_blocks = KeywordRetrievalTool().run(query=search_query)
                # We need to synthesize an answer from these blocks
                context_str = self._format_context_for_prompt(context_blocks)
                answer = self._generate_sub_answer(original_query, search_query, context_str)
                result = {"answer": answer, "source": "keyword_retrieval", "tool_used": "keyword_retrieval"}

            elif tool_to_use == "deep_graph_retrieval":
                # Placeholder for deep graph retrieval logic
                self.logger.warning("Deep graph retrieval is not fully implemented yet.")
                result = {"answer": "Deep graph retrieval not implemented.", "source": "deep_graph_retrieval", "tool_used": "deep_graph_retrieval"}

            elif tool_to_use == "web_search":
                # Tavily tool returns a single string answer
                answer = TavilySearchTool().run(query=search_query)
                result = {"answer": answer, "source": "web_search", "tool_used": "web_search"}
            else:
                self.logger.error(f"Unknown tool recommended by re-planning: {tool_to_use}")
                result = {"answer": "Re-planning failed to select a valid tool.", "source": "re-planning_error", "tool_used": "unknown"}
            
            return result
                
        except Exception as e:
            self.logger.error(f"Error during re-planning: {e}", exc_info=True)
            # As a final fallback, use web search on the original sub-query
            answer = TavilySearchTool().run(query=sub_query)
            return {"answer": answer, "source": "web_search_fallback", "tool_used": "web_search"}

    async def _run_async_logic(self, plan: List[Dict[str, str]], original_query: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Processes the sub-queries in the research plan in parallel.
        """
        logging.info(f"Executing async logic for {len(plan)} sub-queries.")
        tasks = [self._process_one_sub_query(p, original_query) for p in plan]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed_answers = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Handle both old and new planning tool output formats
                sq = plan[i].get('sub_query') or plan[i].get('query', 'Unknown query')
                logging.error(f"An exception occurred while processing sub-query '{sq}': {result}", exc_info=True)
                processed_answers.append({"sub_query": sq, "answer": f"An unexpected error occurred: {result}"})
            else:
                processed_answers.append(result)

        logging.info(f"Parallel research complete. Produced {len(processed_answers)} sub-answers.")
        return {"sub_answers": processed_answers}

    def __call__(self, plan: List[Dict[str, str]], original_query: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        The main synchronous entry point for the tool, called by the dispatcher.
        It starts the asyncio event loop to run the parallel research.
        """
        return asyncio.run(self._run_async_logic(plan, original_query)) 

    # === PHASE 3: QUALITY ENHANCEMENT METHODS ===
    
    def _enhance_table_context_quality(self, context_blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Phase 3: Enhance table context quality by ensuring tables are properly formatted
        and have complete information.
        """
        enhanced_blocks = []
        
        for block in context_blocks:
            enhanced_block = block.copy()
            
            # Check if this block contains table data
            primary_item = block.get('primary_item', {})
            if primary_item and 'table_data' in str(primary_item):
                try:
                    # Ensure table formatting is optimal
                    if hasattr(self, '_format_json_table_to_markdown'):
                        # Table formatting is already handled in _format_context_for_prompt
                        pass
                    
                    # Add table context validation
                    if 'text' in primary_item:
                        text = primary_item['text']
                        if 'Table' in text and len(text) < 100:
                            # Short table references might be incomplete
                            logging.info("Phase 3: Detected potentially incomplete table context")
                            
                except Exception as e:
                    logging.warning(f"Phase 3: Table context enhancement failed: {e}")
            
            enhanced_blocks.append(enhanced_block)
        
        return enhanced_blocks
    
    def _validate_context_completeness(self, sub_query: str, context_blocks: List[Dict[str, Any]]) -> bool:
        """
        Phase 3: Validate that context blocks contain sufficient information
        for the specific query type.
        """
        try:
            # Check for equation queries
            if self._contains_equation_reference(sub_query):
                # Ensure we have mathematical content
                has_math_content = any(
                    'latex' in str(block).lower() or 'equation' in str(block).lower()
                    for block in context_blocks
                )
                if not has_math_content:
                    logging.info("Phase 3: Equation query missing mathematical content")
                    return False
            
            # Check for table queries
            table_ref = self._extract_subsection_from_table_reference(sub_query)
            if table_ref:
                # Ensure we have table content
                has_table_content = any(
                    'table_data' in str(block).lower() or 'table' in str(block).lower()
                    for block in context_blocks
                )
                if not has_table_content:
                    logging.info("Phase 3: Table query missing table content")
                    return False
            
            return True
            
        except Exception as e:
            logging.warning(f"Phase 3: Context completeness validation failed: {e}")
            return True  # Default to True to avoid breaking the workflow
    
    def _apply_phase3_quality_enhancements(self, sub_query: str, context_blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Phase 3: Apply quality enhancements to context blocks.
        This is a safe wrapper that applies enhancements without breaking the system.
        """
        try:
            # Apply table context enhancements
            enhanced_blocks = self._enhance_table_context_quality(context_blocks)
            
            # Validate completeness
            is_complete = self._validate_context_completeness(sub_query, enhanced_blocks)
            if not is_complete:
                logging.info("Phase 3: Context completeness check suggests additional context needed")
            
            return enhanced_blocks
            
        except Exception as e:
            logging.error(f"Phase 3: Quality enhancement failed, using original context: {e}")
            return context_blocks  # Return original on any error
    
    def _detect_and_retrieve_missing_tables(self, context_blocks: List[Dict[str, Any]], sub_query: str) -> List[Dict[str, Any]]:
        """
        Context-aware table detection: Scan context for table references and retrieve missing tables.
        This addresses the issue where table references appear in context but tables aren't retrieved.
        """
        try:
            # Extract all text content from context blocks
            all_context_text = ""
            for block in context_blocks:
                primary_item = block.get('primary_item', {})
                if primary_item and 'text' in primary_item:
                    all_context_text += " " + str(primary_item['text'])
                
                # Also check children
                children = block.get('children', [])
                for child in children:
                    if isinstance(child, dict) and 'text' in child:
                        all_context_text += " " + str(child['text'])
            
            # Find table references in the context text
            table_pattern = r'Table\s+(\d+(?:\.\d+)+)'
            table_matches = re.findall(table_pattern, all_context_text, re.IGNORECASE)
            
            if not table_matches:
                return context_blocks  # No table references found
            
            # Remove duplicates and log findings
            unique_tables = list(set(table_matches))
            logging.info(f"Context-aware table detection found: {unique_tables}")
            
            # Retrieve each missing table
            enhanced_blocks = context_blocks.copy()
            for table_ref in unique_tables:
                try:
                    # Check if we already have this table in context
                    table_already_present = any(
                        f"Table {table_ref}" in str(block).lower() and 
                        ('table_data' in str(block).lower() or 'rows' in str(block).lower())
                        for block in context_blocks
                    )
                    
                    if not table_already_present:
                        logging.info(f"Retrieving missing table: Table {table_ref}")
                        table_context = self._get_subsection_with_all_nodes(table_ref)
                        if table_context:
                            enhanced_blocks.extend(table_context)
                            logging.info(f"Successfully added context for Table {table_ref}")
                        else:
                            logging.warning(f"Could not retrieve context for Table {table_ref}")
                    else:
                        logging.info(f"Table {table_ref} already present in context")
                        
                except Exception as e:
                    logging.warning(f"Error retrieving Table {table_ref}: {e}")
                    continue
            
            return enhanced_blocks
            
        except Exception as e:
            logging.error(f"Context-aware table detection failed: {e}")
            return context_blocks  # Return original on any error 

    def _detect_and_retrieve_missing_diagrams(self, context_blocks: List[Dict[str, Any]], sub_query: str) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Scans retrieved text for references to diagrams (e.g., "Diagram 1611.1")
        and fetches their full node data from the database, including processing the image.
        """
        all_text = " ".join([str(block.get('text', '')) for block in context_blocks])
        
        # Regex to find references like "Diagram 1611.1" or "Fig. 16-2"
        diagram_refs = re.findall(r'(?:Diagram|Figure|Fig\.)\s*([\d\w\.-]+)', all_text, re.IGNORECASE)
        
        if not diagram_refs:
            return context_blocks, []

        self.logger.info(f"Context-aware diagram detection found: {diagram_refs}")
        
        processed_diagrams = []
        for ref in set(diagram_refs):
            # We construct a UID pattern that the diagram would likely have.
            # Example: "Diagram-1611.1-..."
            diagram_uid_pattern = f"Diagram-{ref}"
            
            # Fetch the diagram node from Neo4j
            diagram_node = Neo4jConnector.get_node_by_uid_pattern(diagram_uid_pattern)

            if diagram_node:
                self.logger.info(f"Retrieving missing diagram: {diagram_uid_pattern}")
                
                # Process the image using our utility
                processed_image_data = process_image_for_llm(diagram_node.get("path"))
                
                if processed_image_data:
                    # Append all necessary data for the synthesis agent
                    processed_diagrams.append({
                        "uid": diagram_node.get("uid"),
                        "description": diagram_node.get("description"),
                        "image_data": processed_image_data
                    })
        
        return context_blocks, processed_diagrams

    async def _optimize_query_for_web_search(self, sub_query: str, original_query: str, context_str: str) -> str:
        """
        Optimizes a web search query using LLM for better Tavily results.
        
        This method generates web search queries that are:
        1. Within 400 character limit (Tavily constraint)
        2. Optimized for public web content rather than building codes
        3. Context-aware based on what internal search failed to find
        
        Args:
            sub_query: The original sub-query that failed internal search
            original_query: The user's original query for context
            context_str: Available internal context that was insufficient
            
        Returns:
            Optimized web search query (≤400 characters)
        """
        logging.info(f"Optimizing query for web search: '{sub_query[:50]}...'")
        
        # Fallback: if LLM optimization fails, use truncated sub_query
        fallback_query = sub_query[:397] + "..." if len(sub_query) > 400 else sub_query
        
        try:
            optimization_prompt = f"""Generate an optimized web search query for the Tavily API.

CONSTRAINTS:
- Maximum 400 characters (strictly enforced)
- Target public web resources, not internal building codes
- Focus on concepts that supplement internal research gaps

ORIGINAL USER QUERY: {original_query}

SUB-QUERY THAT FAILED: {sub_query}

AVAILABLE INTERNAL CONTEXT:
{context_str[:500]}...

OPTIMIZATION GOALS:
1. Search for industry standards, best practices, or examples
2. Look for explanatory content that clarifies building code concepts
3. Find authoritative sources (NFPA, ICC, government sites)
4. Use terminology that yields general building/construction information

Generate a focused web search query that will find supplementary information to help answer the user's question. The query should be significantly different from the original sub-query to access different information sources.

RESPOND WITH ONLY THE OPTIMIZED QUERY (≤400 chars):"""

            model = genai.GenerativeModel(TIER_2_MODEL_NAME)
            response = await asyncio.to_thread(model.generate_content, optimization_prompt)
            
            if response and response.text:
                optimized_query = response.text.strip()
                
                # Remove quotes if LLM added them
                if optimized_query.startswith('"') and optimized_query.endswith('"'):
                    optimized_query = optimized_query[1:-1]
                
                # Enforce character limit
                if len(optimized_query) > 400:
                    optimized_query = optimized_query[:397] + "..."
                    logging.warning(f"Truncated optimized query to 400 characters")
                
                # Validate the query isn't empty or too short
                if len(optimized_query.strip()) < 10:
                    logging.warning("Optimized query too short, using fallback")
                    return fallback_query
                
                logging.info(f"✅ Optimized web query ({len(optimized_query)} chars): '{optimized_query}'")
                return optimized_query
            else:
                logging.warning("LLM returned empty response, using fallback query")
                return fallback_query
                
        except Exception as e:
            logging.warning(f"Query optimization failed: {e}, using fallback query")
            return fallback_query 