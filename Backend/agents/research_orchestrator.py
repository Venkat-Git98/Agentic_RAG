"""
Research Orchestrator Agent for LangGraph workflow.

This agent integrates sophisticated research logic with sequential, validation-driven
workflow that includes:
- LLM-driven retrieval strategy selection  
- Sequential fallback hierarchy (direct_retrieval → placeholder; vector → keyword → placeholder)
- ValidationAgent for result quality assessment
- Web search as last resort
- Graph expansion after successful retrieval
"""

import asyncio
import json
from typing import Dict, Any, List
import time

# Add parent directories to path for imports
from .base_agent import BaseLangGraphAgent
from state import AgentState
from state_keys import (
    USER_QUERY, ORIGINAL_QUERY, RESEARCH_PLAN, SUB_QUERY_ANSWERS,
    CURRENT_STEP, WORKFLOW_STATUS, INTERMEDIATE_OUTPUTS,
    QUALITY_METRICS
)

# Import research tools and agents
from tools.parallel_research_tool import ParallelResearchTool
from tools.web_search_tool import TavilySearchTool
from tools.keyword_retrieval_tool import KeywordRetrievalTool
from tools.reranker import Reranker
from config import USE_RERANKER, USE_PARALLEL_EXECUTION, redis_client
from agents.retrieval_strategy_agent import RetrievalStrategyAgent
from thinking_agents.thinking_validation_agent import ThinkingValidationAgent
from tools.neo4j_connector import Neo4jConnector
from tools.equation_detector import EquationDetector

class ResearchOrchestrator(BaseLangGraphAgent):
    """
    Research Orchestrator Agent for sophisticated sequential research execution.
    
    This agent implements a new research paradigm:
    1. LLM determines optimal retrieval strategy 
    2. Sequential execution with validation-driven fallbacks
    3. Web search as last resort
    4. Optional graph expansion on successful retrieval
    """
    
    def __init__(self, llm=None):
        """Initialize the research orchestrator with retrieval tools and agents."""
        super().__init__(
            model_tier="tier_1",
            agent_name="ResearchOrchestrator"
        )
        
        # Initialize tools and agents
        self.retrieval_strategy_agent = RetrievalStrategyAgent()
        self.thinking_validation_agent = ThinkingValidationAgent()
        self.neo4j_connector = Neo4jConnector()
        self.web_search_tool = TavilySearchTool()
        self.equation_detector = EquationDetector()
        
        # Validation threshold for considering context as "relevant"
        self.validation_threshold = 6.0
        
        # Store the LLM for sub-agents
        self.llm = llm or self.model
        
        # Initialize the research tools
        self.research_tool = ParallelResearchTool()
        self.keyword_tool = KeywordRetrievalTool()
        
        # Conditionally initialize reranker based on configuration
        if USE_RERANKER:
            try:
                self.reranker = Reranker()
                self.logger.info("Reranker initialized and enabled")
            except Exception as e:
                self.logger.warning(f"Failed to initialize reranker: {e}. Continuing without reranker.")
                self.reranker = None
        else:
            self.reranker = None
            self.logger.info("Reranker disabled by configuration")
        
        # Set reranker configuration on the research tool
        self.research_tool.reranker = self.reranker
        self.research_tool.use_reranker = USE_RERANKER
        
        execution_mode = "PARALLEL" if USE_PARALLEL_EXECUTION else "SEQUENTIAL"
        self.logger.info(f"Research Orchestrator initialized with {execution_mode} research workflow")
    
    async def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute the research process for each sub-query in the research plan.
        Now supports both parallel and sequential execution modes.
        
        Args:
            state: Current workflow state containing research_plan
            
        Returns:
            Dictionary containing research results and metadata for all sub-queries
        """
        query = state.get(USER_QUERY, "")
        original_query = state.get(ORIGINAL_QUERY, query)
        research_plan = state.get(RESEARCH_PLAN, [])
        
        # Use global configuration for parallel execution
        use_parallel_execution = USE_PARALLEL_EXECUTION
        
        if not research_plan:
            self.logger.warning("Research orchestrator called without a research plan. Using original query.")
            # Fallback to using the original query if no plan exists
            research_plan = [{"sub_query": state.get(USER_QUERY, "")}]

        if use_parallel_execution and len(research_plan) > 1:
            self.logger.info(f"Starting PARALLEL research for {len(research_plan)} sub-queries.")
            return await self._execute_sub_queries_in_parallel(research_plan, original_query)
        else:
            self.logger.info(f"Starting SEQUENTIAL research for {len(research_plan)} sub-queries.")
            return await self._execute_sub_queries_sequentially(research_plan, original_query)

    async def _execute_sub_queries_in_parallel(self, research_plan: List[Dict], original_query: str) -> Dict[str, Any]:
        """
        Execute all sub-queries in parallel using asyncio.gather() for maximum performance.
        This method maintains all mathematical enhancement and validation features.
        
        Args:
            research_plan: List of research plan items with sub_query fields
            original_query: The original user query for context
            
        Returns:
            Dictionary containing research results and metadata for all sub-queries
        """
        try:
            # Create async tasks for all sub-queries
            tasks = []
            for i, plan_item in enumerate(research_plan):
                sub_query = plan_item.get("sub_query")
                if not sub_query:
                    continue
                
                # Create an async task for each sub-query
                task = self._process_single_sub_query_async(sub_query, i, len(research_plan), original_query)
                tasks.append(task)
            
            if not tasks:
                self.logger.warning("No valid sub-queries found in research plan")
                return self._format_final_research_output([])
            
            # Execute all sub-queries in parallel
            self.logger.info(f"Executing {len(tasks)} sub-queries in parallel...")
            start_time = time.time()
            
            # Use asyncio.gather to run all tasks concurrently
            all_sub_answers = await asyncio.gather(*tasks, return_exceptions=True)
            
            total_duration = time.time() - start_time
            self.logger.info(f"--- Parallel research phase complete in {total_duration:.2f}s. Generated {len(all_sub_answers)} sub-answers. ---")
            
            # Handle any exceptions in the results
            processed_answers = []
            for i, result in enumerate(all_sub_answers):
                if isinstance(result, Exception):
                    sub_query = research_plan[i].get("sub_query", "Unknown query")
                    self.logger.error(f"Exception in sub-query {i+1}: {result}")
                    # Create a fallback answer for failed sub-queries
                    processed_answers.append({
                        "sub_query": sub_query,
                        "answer": f"Error processing sub-query: {str(result)}",
                        "sources_used": ["Error"],
                        "retrieval_strategy": "error",
                        "validation_score": 0.0,
                        "is_relevant": False,
                        "reasoning": f"Exception occurred: {str(result)}"
                    })
                else:
                    processed_answers.append(result)
            
            return self._format_final_research_output(processed_answers)
            
        except Exception as e:
            self.logger.error(f"Error in parallel research orchestration: {e}")
            return {
                "error_state": {
                    "agent": self.agent_name,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "timestamp": "now"
                },
                CURRENT_STEP: "error",
                WORKFLOW_STATUS: "failed"
            }

    async def _process_single_sub_query_async(self, sub_query: str, index: int, total: int, original_query: str) -> Dict[str, Any]:
        """
        Process a single sub-query asynchronously with full mathematical enhancement and validation.
        This method encapsulates the complete sub-query processing pipeline.
        
        Args:
            sub_query: The sub-query to process
            index: Index of this sub-query (for logging)
            total: Total number of sub-queries (for logging)
            original_query: Original user query for context
            
        Returns:
            Dictionary containing sub-query results and metadata
        """
        import time
        start_time = time.time()
        self.logger.info(f"--- Processing sub-query {index+1}/{total}: '{sub_query[:100]}...' ---")

        try:
            # Step 1: Determine optimal retrieval strategy for the sub-query
            strategy_result = await self._determine_retrieval_strategy(sub_query, {"query": sub_query})
            strategy = strategy_result.get('retrieval_strategy', 'vector_search')
            self.logger.info(f"Sub-query {index+1} - LLM selected retrieval strategy: {strategy}")

            # Step 2: Execute retrieval with enhanced fallbacks (validation is now done internally)
            retrieved_context = await self._execute_retrieval_with_fallbacks(strategy, sub_query)

            # Step 3: Validate the final retrieved context quality
            validation_result = await self._validate_context_quality(sub_query, retrieved_context)

            # Step 4: Optional graph expansion (only if validation passed)
            if validation_result.get('is_relevant', False):
                retrieved_context = await self._optional_graph_expansion(sub_query, retrieved_context)

            # Step 5: Format the result for this sub-query
            sub_answer = self._format_single_sub_answer(
                sub_query, retrieved_context, validation_result, strategy
            )
            
            duration = time.time() - start_time
            self.logger.info(f"--- Sub-query {index+1} completed in {duration:.2f}s ---")
            return sub_answer
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"Error processing sub-query {index+1} after {duration:.2f}s: {e}")
            return {
                "sub_query": sub_query,
                "answer": f"Error processing sub-query: {str(e)}",
                "sources_used": ["Error"],
                "retrieval_strategy": "error",
                "validation_score": 0.0,
                "is_relevant": False,
                "reasoning": f"Exception occurred: {str(e)}"
            }

    async def _execute_sub_queries_sequentially(self, research_plan: List[Dict], original_query: str) -> Dict[str, Any]:
        """
        Execute sub-queries sequentially (the original implementation).
        Kept for backward compatibility and debugging purposes.
        
        Args:
            research_plan: List of research plan items with sub_query fields
            original_query: The original user query for context
            
        Returns:
            Dictionary containing research results and metadata for all sub-queries
        """
        all_sub_answers = []
        
        try:
            for i, plan_item in enumerate(research_plan):
                sub_query = plan_item.get("sub_query")
                if not sub_query:
                    continue

                # Process each sub-query individually (original sequential logic)
                sub_answer = await self._process_single_sub_query_async(sub_query, i, len(research_plan), original_query)
                all_sub_answers.append(sub_answer)

            self.logger.info(f"--- Sequential research phase complete. Generated {len(all_sub_answers)} sub-answers. ---")
            return self._format_final_research_output(all_sub_answers)
            
        except Exception as e:
            self.logger.error(f"Error in sequential research orchestration: {e}")
            return {
                "error_state": {
                    "agent": self.agent_name,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "timestamp": "now"
                },
                CURRENT_STEP: "error",
                WORKFLOW_STATUS: "failed"
            }
    
    async def _determine_retrieval_strategy(self, query: str, state: AgentState) -> Dict[str, Any]:
        """Use RetrievalStrategyAgent to determine optimal strategy with rule-based fallback."""
        try:
            strategy_state = {
                "query": query,
                "conversation_history": state.get("conversation_history", []),
                "context": state.get("context", "")
            }
            result = await self.retrieval_strategy_agent.execute(strategy_state)
            return result
        except Exception as e:
            self.logger.warning(f"RetrievalStrategyAgent failed: {e}. Using rule-based fallback.")
            # Rule-based fallback strategy
            strategy = self._rule_based_strategy_selection(query)
            self.logger.info(f"Rule-based fallback selected: {strategy}")
            return {"retrieval_strategy": strategy}
    
    def _rule_based_strategy_selection(self, query: str) -> str:
        """
        Simple rule-based strategy selection as fallback when LLM agent fails.
        """
        query_lower = query.lower()
        
        # Rule 1: Direct retrieval for specific section references
        import re
        section_pattern = r'section\s+(\d+\.[\d\.]*)'
        if re.search(section_pattern, query, re.IGNORECASE):
            return "direct_retrieval"
        
        # Rule 2: Keyword search for technical terms and proper nouns
        technical_terms = [
            'asce', 'astm', 'iso', 'ansi', 'nfpa',  # Standards
            'equation', 'table', 'figure', 'diagram',  # Specific references
            'kll', 'moment-resisting', 'cross-laminated', 'fire-retardant'  # Technical terms
        ]
        
        if any(term in query_lower for term in technical_terms):
            return "keyword_search"
        
        # Rule 3: Default to vector search for conceptual queries
        return "vector_search"

    async def _execute_retrieval_with_fallbacks(self, initial_strategy: str, query: str) -> str:
        """Execute retrieval with appropriate fallback sequence based on initial strategy."""
        
        if initial_strategy == "direct_retrieval":
            return await self._try_direct_then_placeholder(query)
        elif initial_strategy == "vector_search":
            # Use the NEW complete fallback hierarchy
            return await self._try_vector_then_keyword_then_direct_then_web(query)
        elif initial_strategy == "keyword_search":
            # Use the NEW complete fallback hierarchy (skipping vector since keyword was chosen first)
            return await self._try_keyword_then_direct_then_web(query)
        else:
            # Default fallback with complete hierarchy
            return await self._try_vector_then_keyword_then_direct_then_web(query)

    async def _try_direct_then_placeholder(self, query: str) -> str:
        """Enhanced direct retrieval with mathematical content detection and fallback."""
        try:
            # First, detect any mathematical content references in the query
            equation_analysis = self.equation_detector.resolve_equation_references(query)
            self.logger.info(f"Equation analysis: {len(equation_analysis['equation_references'])} equation refs, "
                           f"{len(equation_analysis['context_sections'])} sections detected")
            
            # Extract section number from query for direct lookup
            section_id = self._extract_section_id(query)
            if section_id:
                self.logger.info(f"Attempting enhanced direct lookup for section: '{section_id}'")
                
                # Use enhanced query that includes Math, Diagram, and Table nodes
                context = await self._safe_tool_call(
                    self.neo4j_connector.get_enhanced_subsection_context, 
                    section_id
                )
                
                if context and self._is_context_sufficient(str(context)):
                    # Format the enhanced context
                    formatted_context = self._format_enhanced_context(context, equation_analysis)
                    self.logger.info("Enhanced direct subsection lookup successful")
                    return formatted_context
                else:
                    self.logger.info(f"Enhanced direct lookup for '{section_id}' returned insufficient content")
            
            # ENHANCED: Try equation-specific retrieval if we have equation references
            elif equation_analysis['equation_references']:
                self.logger.info("No direct section found, but detected equation references - trying equation-specific retrieval")
                
                # Check if we have resolved equations from the detector
                if equation_analysis['resolved_equations']:
                    self.logger.info(f"Found {len(equation_analysis['resolved_equations'])} resolved equations")
                    equations_context = self.equation_detector.format_equations_for_context(
                        equation_analysis['resolved_equations']
                    )
                    if self._is_context_sufficient(equations_context):
                        return equations_context
                
                # If we have context sections, retrieve from those
                if equation_analysis['context_sections']:
                    self.logger.info(f"Trying contextual sections: {equation_analysis['context_sections']}")
                    combined_context = await self._retrieve_mathematical_context(equation_analysis)
                    if self._is_context_sufficient(combined_context):
                        return combined_context
                
                # ENHANCED: Try targeted equation search using equation numbers
                equation_refs = equation_analysis['equation_references']
                for eq_ref in equation_refs:
                    eq_number = eq_ref['number']
                    self.logger.info(f"Searching for equation pattern: {eq_number}")
                    
                    # Use equation detector to find math nodes
                    equations = self.equation_detector.find_math_by_pattern(eq_number)
                    if equations:
                        equations_text = self.equation_detector.format_equations_for_context(equations)
                        if self._is_context_sufficient(equations_text):
                            self.logger.info(f"Found equations for pattern {eq_number}")
                            return equations_text
            
            # If no specific section, but we detected contextual sections, try contextual retrieval
            elif equation_analysis['context_sections']:
                self.logger.info("No direct section found, but detected contextual sections for equation lookup")
                combined_context = await self._retrieve_mathematical_context(equation_analysis)
                if self._is_context_sufficient(combined_context):
                    return combined_context
            
            else:
                self.logger.warning(f"Could not extract section ID from query: '{query}'")
                
        except Exception as e:
            self.logger.warning(f"Enhanced direct retrieval failed: {e}")
        
        self.logger.info("Enhanced direct retrieval insufficient. Falling back to vector search.")
        return await self._try_vector_search_fallback(query)
    
    async def _retrieve_mathematical_context(self, equation_analysis: Dict[str, Any]) -> str:
        """
        Retrieve mathematical content based on equation analysis.
        Enhanced with multiple retrieval strategies and better error handling.
        
        Args:
            equation_analysis: Results from equation detector
            
        Returns:
            Formatted context string with mathematical content
        """
        combined_context = []
        
        # Strategy 1: Get content from detected sections using enhanced queries
        for section in equation_analysis['context_sections'][:5]:  # Increased limit
            try:
                self.logger.info(f"Trying enhanced subsection context for: {section}")
                context = await self._safe_tool_call(
                    self.neo4j_connector.get_enhanced_subsection_context,
                    section
                )
                if context:
                    formatted = self._format_enhanced_context(context, equation_analysis)
                    if self._is_context_sufficient(formatted):
                        combined_context.append(formatted)
                        self.logger.info(f"Successfully retrieved context from section {section}")
                    else:
                        self.logger.info(f"Context from section {section} was insufficient")
                else:
                    self.logger.info(f"No context returned for section {section}")
            except Exception as e:
                self.logger.warning(f"Failed to retrieve context for section {section}: {e}")
        
        # Strategy 2: Add any resolved equations directly
        if equation_analysis['resolved_equations']:
            self.logger.info(f"Adding {len(equation_analysis['resolved_equations'])} resolved equations")
            equations_text = self.equation_detector.format_equations_for_context(
                equation_analysis['resolved_equations']
            )
            if equations_text and self._is_context_sufficient(equations_text):
                combined_context.append(equations_text)
        
        # Strategy 3: If we still don't have enough context, try broader searches
        if not combined_context and equation_analysis['equation_references']:
            self.logger.info("No context from sections, trying equation pattern searches")
            for eq_ref in equation_analysis['equation_references']:
                eq_number = eq_ref['number']
                equations = self.equation_detector.find_math_by_pattern(eq_number)
                if equations:
                    equations_text = self.equation_detector.format_equations_for_context(equations)
                    if equations_text:
                        combined_context.append(equations_text)
                        self.logger.info(f"Found equations for pattern {eq_number}")
                        break  # Found something, use it
        
        # Strategy 4: If still no context, try chapter-level retrieval
        if not combined_context and equation_analysis['equation_references']:
            for eq_ref in equation_analysis['equation_references']:
                eq_number = eq_ref['number']
                # Extract chapter number (e.g., "16-7" -> "16")
                import re
                chapter_match = re.match(r'(\d+)', eq_number)
                if chapter_match:
                    chapter_num = chapter_match.group(1)
                    self.logger.info(f"Trying chapter-level retrieval for chapter {chapter_num}")
                    try:
                        equations = self.equation_detector.get_equations_by_chapter(chapter_num)
                        if equations:
                            # Filter to equations that might match our pattern
                            filtered_equations = [eq for eq in equations if eq_number.replace('-', '.') in eq.get('uid', '')]
                            if filtered_equations:
                                equations_text = self.equation_detector.format_equations_for_context(filtered_equations)
                                if equations_text:
                                    combined_context.append(equations_text)
                                    self.logger.info(f"Found {len(filtered_equations)} matching equations in chapter {chapter_num}")
                                    break
                    except Exception as e:
                        self.logger.warning(f"Chapter-level retrieval failed for chapter {chapter_num}: {e}")
        
        result = "\n\n---\n\n".join(combined_context) if combined_context else ""
        
        if result:
            self.logger.info(f"Mathematical context retrieval successful: {len(result)} characters")
        else:
            self.logger.warning("Mathematical context retrieval failed to find any content")
            
        return result
    
    def _format_enhanced_context(self, context: Dict[str, Any], equation_analysis: Dict[str, Any] = None) -> str:
        """
        Format enhanced context that includes Math, Diagram, and Table nodes.
        
        Args:
            context: Context dictionary from enhanced query
            equation_analysis: Optional equation analysis results
            
        Returns:
            Formatted context string
        """
        if not context:
            return "No context available"
        
        formatted_parts = []
        
        # Handle chapter overview format (primary_item structure)
        primary_item = context.get('primary_item')
        if primary_item:
            formatted_parts.append(f"=== {primary_item.get('type', '').upper()} {primary_item.get('number', '')} ===")
            if primary_item.get('title'):
                formatted_parts.append(f"Title: {primary_item['title']}")
            if primary_item.get('text'):
                formatted_parts.append(f"Content: {primary_item['text']}")
            
            # ENHANCED: Add supplemental context with comprehensive content aggregation
            supplemental = context.get('supplemental_context', {})
            if isinstance(supplemental, dict):
                
                # Process passages (main content) - These contain the actual section text
                passages = supplemental.get('passages', [])
                if passages:
                    formatted_parts.append(f"\n=== SECTION CONTENT ===")
                    for passage in passages:
                        if isinstance(passage, dict):
                            passage_text = passage.get('text', '')
                            passage_title = passage.get('title', '')
                            passage_uid = passage.get('uid', '')
                            
                            # Include the actual text content (this is the main content!)
                            if passage_text:
                                if passage_title and passage_title != passage_text:
                                    formatted_parts.append(f"\n{passage_title}")
                                formatted_parts.append(passage_text)
                            elif passage_title:  # Include title even if no text
                                formatted_parts.append(f"\n{passage_title}")
                
                # Process mathematical content with full details
                math_content = supplemental.get('mathematical_content', [])
                if math_content:
                    formatted_parts.append(f"\n=== MATHEMATICAL EQUATIONS ===")
                    for i, math_item in enumerate(math_content, 1):
                        if isinstance(math_item, dict):
                            latex = math_item.get('latex', '')
                            uid = math_item.get('uid', f'equation-{i}')
                            if latex:
                                formatted_parts.append(f"Equation {i} (ID: {uid}): {latex}")
                
                # Process tables with full content
                tables = supplemental.get('tables', [])
                if tables:
                    formatted_parts.append(f"\n=== TABLES ===")
                    for table in tables:
                        if isinstance(table, dict):
                            title = table.get('title', 'Table')
                            headers = table.get('headers', '')
                            rows = table.get('rows', [])
                            uid = table.get('uid', '')
                            html_repr = table.get('html_repr', '')
                            
                            formatted_parts.append(f"\n{title} (ID: {uid})")
                            if headers:
                                formatted_parts.append(f"Headers: {headers}")
                            if rows:
                                formatted_parts.append(f"Rows: {len(rows)} rows of data")
                            if html_repr and html_repr != title:
                                formatted_parts.append(html_repr[:500] + "..." if len(html_repr) > 500 else html_repr)
                
                # Process diagrams with descriptions
                diagrams = supplemental.get('diagrams', [])
                if diagrams:
                    formatted_parts.append(f"\n=== DIAGRAMS ===")
                    for diagram in diagrams:
                        if isinstance(diagram, dict):
                            description = diagram.get('description', '')
                            path = diagram.get('path', '')
                            uid = diagram.get('uid', '')
                            
                            if description:
                                formatted_parts.append(f"Diagram (ID: {uid}): {description}")
                            if path:
                                formatted_parts.append(f"  File: {path}")
                
                # Process any other content types (sections, etc.)
                for key, items in supplemental.items():
                    if key not in ['passages', 'mathematical_content', 'tables', 'diagrams'] and items:
                        if isinstance(items, list):
                            formatted_parts.append(f"\n=== {key.upper().replace('_', ' ')} ===")
                            for item in items:
                                if isinstance(item, dict):
                                    title = item.get('title', '')
                                    text = item.get('text', '')
                                    number = item.get('number', '')
                                    
                                    if title or text:
                                        display_text = f"{number}: {title}" if number and title else (title or text)
                                        formatted_parts.append(f"- {display_text}")
                                        # Include text content if different from title
                                        if text and text != title and len(text) > 10:
                                            formatted_parts.append(f"  {text}")
            
            return "\n".join(formatted_parts)
        
        # Handle enhanced subsection format (parent structure)
        parent = context.get('parent')
        if parent:
            formatted_parts.append(f"=== SECTION {parent.get('number', '')} ===")
            if parent.get('title'):
                formatted_parts.append(f"Title: {parent['title']}")
            if parent.get('text'):
                formatted_parts.append(f"Content: {parent['text']}")
        
        # Add regular content nodes
        content_nodes = context.get('content_nodes', [])
        if content_nodes:
            formatted_parts.append("\n=== CONTENT ===")
            for node in content_nodes:
                if hasattr(node, 'text') and node.text:
                    formatted_parts.append(node.text)
                elif isinstance(node, dict) and node.get('text'):
                    formatted_parts.append(node['text'])
        
        # Add mathematical content
        math_nodes = context.get('math_nodes', [])
        if math_nodes:
            formatted_parts.append("\n=== MATHEMATICAL EQUATIONS ===")
            for i, math_node in enumerate(math_nodes, 1):
                if hasattr(math_node, 'latex'):
                    formatted_parts.append(f"Equation {i} (ID: {math_node.uid}): {math_node.latex}")
                elif isinstance(math_node, dict):
                    uid = math_node.get('uid', f'equation-{i}')
                    latex = math_node.get('latex', 'No LaTeX available')
                    formatted_parts.append(f"Equation {i} (ID: {uid}): {latex}")
        
        # Add diagrams
        diagram_nodes = context.get('diagram_nodes', [])
        if diagram_nodes:
            formatted_parts.append("\n=== DIAGRAMS ===")
            for i, diagram in enumerate(diagram_nodes, 1):
                if hasattr(diagram, 'description'):
                    formatted_parts.append(f"Diagram {i} (ID: {diagram.uid}): {diagram.description}")
                elif isinstance(diagram, dict):
                    uid = diagram.get('uid', f'diagram-{i}')
                    desc = diagram.get('description', 'No description available')
                    formatted_parts.append(f"Diagram {i} (ID: {uid}): {desc}")
        
        # Add tables
        table_nodes = context.get('table_nodes', [])
        if table_nodes:
            formatted_parts.append("\n=== TABLES ===")
            for i, table in enumerate(table_nodes, 1):
                if hasattr(table, 'title'):
                    title = table.title or f"Table {i}"
                    formatted_parts.append(f"{title} (ID: {table.uid})")
                    if hasattr(table, 'headers') and table.headers:
                        formatted_parts.append(f"Headers: {table.headers}")
                elif isinstance(table, dict):
                    uid = table.get('uid', f'table-{i}')
                    title = table.get('title', f'Table {i}')
                    headers = table.get('headers', '')
                    formatted_parts.append(f"{title} (ID: {uid})")
                    if headers:
                        formatted_parts.append(f"Headers: {headers}")
        
        # Add referenced content
        ref_math = context.get('referenced_math', [])
        ref_tables = context.get('referenced_tables', [])
        if ref_math or ref_tables:
            formatted_parts.append("\n=== REFERENCED CONTENT ===")
            for math in ref_math:
                if hasattr(math, 'latex'):
                    formatted_parts.append(f"Referenced Equation (ID: {math.uid}): {math.latex}")
            for table in ref_tables:
                if hasattr(table, 'title'):
                    formatted_parts.append(f"Referenced Table (ID: {table.uid}): {table.title}")
        
        return "\n".join(formatted_parts)
    
    def _extract_section_id(self, query: str) -> str:
        """Extract section ID from a query for direct retrieval."""
        import re
        
        # Pattern to match section references like "1607.12.1"
        section_pattern = r'section\s+(\d+\.[\d\.]*)'
        match = re.search(section_pattern, query, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # Also try pattern without "section" keyword for queries like "What is 1607.12.1?"
        standalone_pattern = r'\b(\d+\.[\d\.]+)\b'
        match = re.search(standalone_pattern, query)
        if match:
            return match.group(1)
        
        # ENHANCED: Try to extract section from equation references
        # E.g., "Equation 16-7" should try sections like "1607", "1607.12", etc.
        equation_pattern = r'equation\s+(\d+)[-\.](\d+)'
        match = re.search(equation_pattern, query, re.IGNORECASE)
        if match:
            chapter = match.group(1)
            eq_num = match.group(2)
            # Try common section patterns for this chapter
            potential_sections = [
                f"{chapter}07.12.1",  # Most specific first
                f"{chapter}07.12", 
                f"{chapter}07",
                f"{chapter}",
            ]
            self.logger.info(f"Extracted equation {chapter}-{eq_num}, will try sections: {potential_sections}")
            # Return the first potential section (most specific)
            return potential_sections[0]
        
        # ENHANCED: Try to extract section from table references
        # E.g., "Table 1607.1" should try section "1607.1"
        table_pattern = r'table\s+(\d+\.[\d\.]*)'
        match = re.search(table_pattern, query, re.IGNORECASE)
        if match:
            section_from_table = match.group(1)
            self.logger.info(f"Extracted section {section_from_table} from table reference")
            return section_from_table
        
        return None
    
    async def _try_vector_then_keyword_then_placeholder(self, query: str) -> str:
        """Vector → Keyword → Web Search fallback sequence."""
        # Try vector search first
        try:
            self.logger.info(f"Attempting vector search for: '{query}'")
            embedding = self._get_embedding(query)
            context_blocks = await self._safe_tool_call(self.neo4j_connector.vector_search, embedding, 3)
            formatted_context = self._format_context_blocks(context_blocks)
            if self._is_context_sufficient(formatted_context):
                self.logger.info("Vector search successful")
                return formatted_context
        except Exception as e:
            self.logger.warning(f"Vector search failed: {e}")
        
        # Fall back to keyword search using the proper KeywordRetrievalTool
        try:
            self.logger.info("Vector search insufficient. Trying keyword search.")
            context = await self._safe_tool_call(self.keyword_tool, query)
            if self._is_context_sufficient(context):
                self.logger.info("Keyword search successful")
                return context
        except Exception as e:
            self.logger.warning(f"Keyword search failed: {e}")

        # Final fallback to web search
        self.logger.info("Keyword search insufficient. Falling back to web search.")
        return await self._try_web_search_fallback(query)

    async def _try_keyword_then_placeholder(self, query: str) -> str:
        """Keyword → Web Search fallback sequence."""
        try:
            self.logger.info(f"Attempting keyword search for: '{query}'")
            context = await self._safe_tool_call(self.keyword_tool, query)
            if self._is_context_sufficient(context):
                self.logger.info("Keyword search successful")
                return context
        except Exception as e:
            self.logger.warning(f"Keyword search failed: {e}")

        self.logger.info("Keyword search insufficient. Falling back to web search.")
        return await self._try_web_search_fallback(query)

    async def _try_vector_search_fallback(self, query: str) -> str:
        """Vector search fallback."""
        try:
            self.logger.info(f"Vector search fallback for: '{query}'")
            embedding = self._get_embedding(query)
            context_blocks = await self._safe_tool_call(self.neo4j_connector.vector_search, embedding, 3)
            formatted_context = self._format_context_blocks(context_blocks)
            if self._is_context_sufficient(formatted_context):
                return formatted_context
        except Exception as e:
            self.logger.error(f"Vector search fallback failed: {e}")
        
        return await self._try_web_search_fallback(query)

    async def _try_vector_then_keyword_then_direct_then_web(self, query: str) -> str:
        """
        Complete fallback hierarchy: Vector → Keyword → Direct Retrieval → Web Search
        This implements the correct logic that was missing from the system.
        Each step includes validation to determine if the next step should be tried.
        """
        # Try vector search first
        try:
            self.logger.info(f"Step 1/4: Attempting vector search for: '{query}'")
            embedding = self._get_embedding(query)
            context_blocks = await self._safe_tool_call(self.neo4j_connector.vector_search, embedding, 3)
            formatted_context = self._format_context_blocks(context_blocks)
            if self._is_context_sufficient(formatted_context):
                # Validate the vector search result before accepting it
                validation_result = await self._validate_context_quality(query, formatted_context)
                if validation_result.get('is_relevant', False):
                    self.logger.info("✅ Vector search successful (passed validation)")
                    return formatted_context
                else:
                    self.logger.info(f"Vector search found context but failed validation (score: {validation_result.get('relevance_score', 0)}/10)")
            else:
                self.logger.info("Vector search returned insufficient context")
        except Exception as e:
            self.logger.warning(f"Vector search failed: {e}")
        
        # Fall back to keyword search using the proper KeywordRetrievalTool
        try:
            self.logger.info("Step 2/4: Vector search insufficient. Trying keyword search.")
            context = await self._safe_tool_call(self.keyword_tool, query)
            if self._is_context_sufficient(context):
                # Validate the keyword search result before accepting it
                validation_result = await self._validate_context_quality(query, context)
                if validation_result.get('is_relevant', False):
                    self.logger.info("✅ Keyword search successful (passed validation)")
                    return context
                else:
                    self.logger.info(f"Keyword search found context but failed validation (score: {validation_result.get('relevance_score', 0)}/10)")
            else:
                self.logger.info("Keyword search returned insufficient context")
        except Exception as e:
            self.logger.warning(f"Keyword search failed: {e}")

        # NEW: Fall back to direct retrieval (table of contents lookup)
        try:
            self.logger.info("Step 3/4: Keyword search insufficient. Trying direct retrieval (table of contents lookup).")
            context = await self._try_direct_retrieval_fallback(query)
            if self._is_context_sufficient(context):
                # Validate the direct retrieval result before accepting it
                validation_result = await self._validate_context_quality(query, context)
                if validation_result.get('is_relevant', False):
                    self.logger.info("✅ Direct retrieval successful (passed validation)")
                    return context
                else:
                    self.logger.info(f"Direct retrieval found context but failed validation (score: {validation_result.get('relevance_score', 0)}/10)")
            else:
                self.logger.info("Direct retrieval returned insufficient context")
        except Exception as e:
            self.logger.warning(f"Direct retrieval failed: {e}")

        # Final fallback to web search
        self.logger.info("Step 4/4: All local retrieval methods failed validation. Falling back to web search.")
        return await self._try_web_search_fallback(query)

    async def _try_keyword_then_direct_then_web(self, query: str) -> str:
        """
        Keyword → Direct Retrieval → Web Search fallback sequence.
        Used when keyword_search is the initial strategy.
        Each step includes validation to determine if the next step should be tried.
        """
        # Fall back to keyword search using the proper KeywordRetrievalTool
        try:
            self.logger.info(f"Step 1/3: Attempting keyword search for: '{query}'")
            context = await self._safe_tool_call(self.keyword_tool, query)
            if self._is_context_sufficient(context):
                # Validate the keyword search result before accepting it
                validation_result = await self._validate_context_quality(query, context)
                if validation_result.get('is_relevant', False):
                    self.logger.info("✅ Keyword search successful (passed validation)")
                    return context
                else:
                    self.logger.info(f"Keyword search found context but failed validation (score: {validation_result.get('relevance_score', 0)}/10)")
            else:
                self.logger.info("Keyword search returned insufficient context")
        except Exception as e:
            self.logger.warning(f"Keyword search failed: {e}")

        # NEW: Fall back to direct retrieval (table of contents lookup)
        try:
            self.logger.info("Step 2/3: Keyword search insufficient. Trying direct retrieval (table of contents lookup).")
            context = await self._try_direct_retrieval_fallback(query)
            if self._is_context_sufficient(context):
                # Validate the direct retrieval result before accepting it
                validation_result = await self._validate_context_quality(query, context)
                if validation_result.get('is_relevant', False):
                    self.logger.info("✅ Direct retrieval successful (passed validation)")
                    return context
                else:
                    self.logger.info(f"Direct retrieval found context but failed validation (score: {validation_result.get('relevance_score', 0)}/10)")
            else:
                self.logger.info("Direct retrieval returned insufficient context")
        except Exception as e:
            self.logger.warning(f"Direct retrieval failed: {e}")

        # Final fallback to web search
        self.logger.info("Step 3/3: All local retrieval methods failed validation. Falling back to web search.")
        return await self._try_web_search_fallback(query)

    async def _llm_extract_relevant_sections(self, query: str) -> List[str]:
        """
        Use LLM to extract relevant chapters and sections from complex queries.
        This enables direct retrieval even when explicit section numbers aren't mentioned.
        """
        try:
            extraction_prompt = f"""
You are an expert in the Virginia Building Code structure. Given this query about building codes, identify the most relevant chapters and sections that would contain the answer.

Query: "{query}"

Based on common Virginia Building Code organization:
- Chapter 16: Structural Design
- Chapter 17: Special Inspections and Tests  
- Chapter 19: Concrete
- Chapter 18: Soils and Foundations
- Chapter 21: Masonry
- Chapter 23: Wood
- Chapter 30: Elevators and Conveying Systems
- Chapter 31: Special Construction
- Section 1607: Live Loads
- Section 1608: Snow Loads
- Section 1609: Wind Loads  
- Section 1613: Earthquake Loads
- Section 1616: Structural Design
- Section 1901-1914: Concrete sections
- Section 1705: Special Inspections

For queries about:
- Hospital/critical facilities: Chapter 3 (Use and Occupancy), Section 1613 (Earthquake loads), Section 1609 (Wind loads)
- Concrete construction: Chapter 19 (sections 1901-1914), Section 1907 (Details), Section 1909 (Structural concrete)
- Structural connections: Section 1907.6 (Connections), Section 1909.4 (Structural integrity), Section 1914 (Shotcrete)
- Cast-in-place concrete: Section 1909 (Structural concrete), Section 1907 (Details and detailing), Section 1908 (Durability)
- Critical facility requirements: Section 1613.1 (Risk category), Section 1609.1.1 (Critical facilities), Section 1705.3 (Structural)
- Load requirements: Chapter 16, sections 1607-1613
- Inspections: Chapter 17, Section 1705

Return a JSON list of the 3-5 most relevant section numbers in order of relevance.
Format: ["16", "1607", "1607.12", "19", "1901"] (chapters as numbers, sections with dots)

Only return the JSON array, no other text.
"""

            # Use the LLM to extract sections
            import google.generativeai as genai
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            
            response = model.generate_content(extraction_prompt)
            response_text = response.text.strip()
            
            # Handle markdown code blocks - extract JSON from ```json ... ```
            if response_text.startswith("```json"):
                # Extract JSON from markdown code block
                start_idx = response_text.find("[")
                end_idx = response_text.rfind("]") + 1
                if start_idx != -1 and end_idx != -1:
                    response_text = response_text[start_idx:end_idx]
            elif response_text.startswith("```"):
                # Extract JSON from generic code block
                start_idx = response_text.find("[")
                end_idx = response_text.rfind("]") + 1
                if start_idx != -1 and end_idx != -1:
                    response_text = response_text[start_idx:end_idx]
            
            # Parse the JSON response
            import json
            try:
                sections = json.loads(response_text)
                if isinstance(sections, list) and sections:
                    self.logger.info(f"LLM extracted relevant sections: {sections}")
                    return sections[:5]  # Limit to top 5
            except json.JSONDecodeError:
                self.logger.warning(f"Failed to parse LLM response as JSON: {response_text}")
                
        except Exception as e:
            self.logger.warning(f"LLM section extraction failed: {e}")
        
        return []
    
    async def _try_direct_retrieval_fallback(self, query: str) -> str:
        """
        Enhanced direct retrieval fallback - uses table of contents structure to find relevant sections.
        Now includes LLM-powered section extraction for complex queries.
        """
        try:
            # First, detect any mathematical content references in the query
            equation_analysis = self.equation_detector.resolve_equation_references(query)
            self.logger.info(f"Direct retrieval fallback - Equation analysis: {len(equation_analysis['equation_references'])} equation refs, "
                           f"{len(equation_analysis['context_sections'])} sections detected")
            
            # Extract section number from query for direct lookup (existing method)
            section_id = self._extract_section_id(query)
            if section_id:
                self.logger.info(f"Direct retrieval - Attempting enhanced direct lookup for section: '{section_id}'")
                
                # Use enhanced query that includes Math, Diagram, and Table nodes
                context = await self._safe_tool_call(
                    self.neo4j_connector.get_enhanced_subsection_context, 
                    section_id
                )
                
                if context and self._is_context_sufficient(str(context)):
                    # Format the enhanced context
                    formatted_context = self._format_enhanced_context(context, equation_analysis)
                    self.logger.info("✅ Direct retrieval - Enhanced direct subsection lookup successful")
                    return formatted_context
                else:
                    self.logger.info(f"Direct retrieval - Enhanced direct lookup for '{section_id}' returned insufficient content")
            
            # NEW: Try LLM-powered section extraction for complex queries
            elif "virginia building code" in query.lower() or "building code" in query.lower():
                self.logger.info("Direct retrieval - No explicit section found, trying LLM-powered section extraction")
                
                relevant_sections = await self._llm_extract_relevant_sections(query)
                if relevant_sections:
                    self.logger.info(f"Direct retrieval - LLM identified relevant sections: {relevant_sections}")
                    
                    # Try each section in order of relevance
                    best_context = None
                    for section in relevant_sections:
                        try:
                            self.logger.info(f"Direct retrieval - Trying section: {section}")
                            
                            # Determine which query to use based on section format
                            context = None
                            
                            if "." not in section and len(section) <= 2:
                                # Chapter-level (e.g., "16", "19") - use chapter overview
                                context = await self._safe_tool_call(
                                    self.neo4j_connector.get_chapter_overview_by_id, 
                                    section
                                )
                            elif "." not in section and len(section) == 4:
                                # Section-level (e.g., "1909", "1907", "1613") - try subsection pattern matching
                                # First try exact subsection match
                                context = await self._safe_tool_call(
                                    self.neo4j_connector.get_enhanced_subsection_context, 
                                    section
                                )
                                
                                # If no exact match, try common subsection patterns
                                if not context or not self._is_context_sufficient(str(context)):
                                    subsection_patterns = [f"{section}.1", f"{section}.2", f"{section}.3", f"{section}.4"]
                                    for pattern in subsection_patterns:
                                        try:
                                            context = await self._safe_tool_call(
                                                self.neo4j_connector.get_enhanced_subsection_context, 
                                                pattern
                                            )
                                            if context and self._is_context_sufficient(str(context)):
                                                self.logger.info(f"Direct retrieval - Found content using pattern: {pattern}")
                                                break
                                        except Exception as e:
                                            continue
                                    
                                    # If still no content, try parent chapter
                                    if not context or not self._is_context_sufficient(str(context)):
                                        parent_chapter = section[:2]  # "1909" -> "19"
                                        self.logger.info(f"Direct retrieval - Falling back to parent chapter: {parent_chapter}")
                                        context = await self._safe_tool_call(
                                            self.neo4j_connector.get_chapter_overview_by_id, 
                                            parent_chapter
                                        )
                                        
                            elif "." in section and len(section.split(".")) <= 3:
                                # Subsection level (e.g., "1607.12", "1607.12.1") - exact match
                                context = await self._safe_tool_call(
                                    self.neo4j_connector.get_enhanced_subsection_context, 
                                    section
                                )
                            else:
                                continue
                                
                            if context and self._is_context_sufficient(str(context)):
                                formatted_context = self._format_enhanced_context(context, equation_analysis)
                                self.logger.info(f"✅ Direct retrieval - LLM-guided lookup successful for section {section}")
                                
                                # Validate the context quality
                                validation_result = await self._validate_context_quality(query, formatted_context)
                                relevance_score = validation_result.get("relevance_score", 1)
                                is_relevant = relevance_score >= 4
                                
                                if is_relevant:
                                    return formatted_context
                                else:
                                    self.logger.info(f"Direct retrieval - Section {section} failed validation (score: {relevance_score}/10)")
                                    # Store the best context we found so far
                                    if not best_context:
                                        best_context = formatted_context
                            else:
                                self.logger.info(f"Direct retrieval - Section {section} returned insufficient content")
                                # Store the best context we found so far
                                if not best_context and context:
                                    formatted_context = self._format_enhanced_context(context, equation_analysis)
                                    validation_result = await self._validate_context_quality(query, formatted_context)
                                    best_context = formatted_context
                                
                        except Exception as e:
                            self.logger.warning(f"Direct retrieval - Failed to retrieve section {section}: {e}")
                            continue
                    
                    # If we didn't find a great match but have some content, use it
                    if best_context:
                        self.logger.info("✅ Direct retrieval - Using best available context")
                        return best_context
                
                else:
                    self.logger.info("Direct retrieval - LLM could not identify relevant sections")
            
            # Try equation-specific retrieval if we have equation references
            if equation_analysis['equation_references']:
                self.logger.info("Direct retrieval - No direct section found, but detected equation references - trying equation-specific retrieval")
                combined_context = await self._retrieve_mathematical_context(equation_analysis)
                if self._is_context_sufficient(combined_context):
                    self.logger.info("✅ Direct retrieval - Mathematical context retrieval successful")
                    return combined_context
            
            # If we have context sections, try contextual retrieval
            if equation_analysis['context_sections']:
                self.logger.info("Direct retrieval - Trying contextual sections for equation lookup")
                combined_context = await self._retrieve_mathematical_context(equation_analysis)
                if self._is_context_sufficient(combined_context):
                    self.logger.info("✅ Direct retrieval - Contextual section retrieval successful")
                    return combined_context
            
            self.logger.warning(f"Direct retrieval - Could not extract any retrievable patterns from query: '{query}'")
            return "No direct retrieval patterns found"
                
        except Exception as e:
            self.logger.warning(f"Direct retrieval fallback failed: {e}")
            return f"Direct retrieval error: {e}"

    def _get_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using the same method as ParallelResearchTool."""
        import google.generativeai as genai
        from config import EMBEDDING_MODEL
        
        try:
            response = genai.embed_content(
                model=EMBEDDING_MODEL, 
                content=text, 
                task_type="RETRIEVAL_DOCUMENT"
            )
            return response['embedding']
        except Exception as e:
            self.logger.error(f"Failed to generate embedding: {e}")
            return []

    def _format_context_blocks(self, context_blocks) -> str:
        """Format context blocks into a readable string."""
        if not context_blocks:
            return "No context found"
        
        if isinstance(context_blocks, dict):
            # Single context dict 
            return str(context_blocks.get('text', str(context_blocks)))
        elif isinstance(context_blocks, list):
            # List of context blocks
            formatted_blocks = []
            for block in context_blocks:
                if isinstance(block, dict):
                    text = block.get('text', str(block))
                    formatted_blocks.append(text)
                else:
                    formatted_blocks.append(str(block))
            return "\n\n".join(formatted_blocks)
        else:
            return str(context_blocks)

    async def _validate_context_quality(self, query: str, context: str) -> Dict[str, Any]:
        """Use ThinkingValidationAgent to validate the quality of the retrieved context."""
        try:
            validation_state = {
                "query": query,
                "context": context
            }
            result = await self.thinking_validation_agent.execute(validation_state)
            validation_result = result.get("validation_result", {"relevance_score": 1, "reasoning": "No validation result"})
            
            # Convert relevance_score to is_relevant boolean
            # Score >= 4 is considered relevant (adjusted threshold for direct retrieval)
            relevance_score = validation_result.get("relevance_score", 1)
            is_relevant = relevance_score >= 4
            
            return {
                "is_relevant": is_relevant,
                "relevance_score": relevance_score,
                "reasoning": validation_result.get("reasoning", "No reasoning provided"),
                "confidence_score": relevance_score / 10.0  # Convert to 0-1 scale
            }
        except Exception as e:
            self.logger.warning(f"ThinkingValidationAgent failed: {e}. Defaulting to not relevant.")
            return {"is_relevant": False, "reasoning": "Validation agent failed."}

    async def _try_web_search_fallback(self, query: str) -> str:
        """Web search as final fallback option."""
        try:
            self.logger.info(f"Attempting web search fallback for: '{query}'")
            result = await self._safe_tool_call(self.web_search_tool, query)
            # TavilySearchTool returns a dict with 'answer' key
            if isinstance(result, dict) and 'answer' in result:
                return result['answer']
            return str(result)
        except Exception as e:
            self.logger.error(f"Web search fallback failed: {e}")
            return f"Unable to retrieve relevant information for query: {query}"

    async def _optional_graph_expansion(self, query: str, context: str) -> str:
        """Optional graph expansion on successful retrieval."""
        # Placeholder for future graph expansion logic
        self.logger.info("Graph expansion placeholder - returning original context")
        return context

    async def _safe_tool_call(self, tool_func, *args, **kwargs):
        """Safely call a tool function with error handling."""
        try:
            # Handle both sync and async tool functions
            if asyncio.iscoroutinefunction(tool_func):
                return await tool_func(*args, **kwargs)
            else:
                return tool_func(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"Tool call failed for {tool_func.__name__}: {e}")
            return f"Tool execution failed: {e}"

    def _is_context_sufficient(self, context: str) -> bool:
        """Check if retrieved context is sufficient."""
        if not context or len(context.strip()) < 10:
            return False
        
        insufficient_indicators = [
            "No information was found",
            "Unable to retrieve", 
            "Tool execution failed",
            "No relevant documents found",
            "No results found"
        ]
        
        # Check for insufficient indicators
        if any(indicator in context for indicator in insufficient_indicators):
            return False
            
        # Accept structured content (JSON-like or contains chapter/section info)
        # ENHANCED: Be more generous with content that contains actual section content
        structured_indicators = [
            "=== SECTION CONTENT ===",
            "=== MATHEMATICAL EQUATIONS ===", 
            "=== TABLES ===",
            "=== DIAGRAMS ===",
            "primary_item",
            "chapter",
            "section",
            "concrete",
            "building code",
            "structural",
            "scope",
            "general"
        ]
        
        has_structure = any(indicator.lower() in context.lower() for indicator in structured_indicators)
        
        if (has_structure or len(context.strip()) > 50):
            return True
            
        return False

    def _format_single_sub_answer(self, query: str, context: str, validation_result: Dict[str, Any], strategy: str) -> Dict[str, Any]:
        """Format a single sub-query answer for LangGraph state update."""
        return {
            "sub_query": query,
            "answer": context,
            "sources_used": ["Research Context"],
            "retrieval_strategy": strategy,
            "validation_score": validation_result.get("confidence_score", 0.0),
            "is_relevant": validation_result.get("is_relevant", False),
            "reasoning": validation_result.get("validation_reasoning", "No reasoning provided")
        }

    def _format_final_research_output(self, all_sub_answers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Format the final research output for LangGraph state update."""
        successful_queries = sum(1 for ans in all_sub_answers if ans.get("is_relevant"))
        total_queries = len(all_sub_answers)
        avg_validation_score = sum(ans.get("validation_score", 0.0) for ans in all_sub_answers) / total_queries if total_queries > 0 else 0.0
        
        return {
            SUB_QUERY_ANSWERS: all_sub_answers,
            "research_context": "\n\n---\n\n".join([a["answer"] for a in all_sub_answers]),
            "validation_reasoning": "\n\n---\n\n".join([a.get("reasoning", "No reasoning") for a in all_sub_answers]),
            "retrieval_strategy_used": all_sub_answers[0]["retrieval_strategy"] if all_sub_answers else "N/A",
            "research_quality_score": avg_validation_score,
            CURRENT_STEP: "synthesis",
            WORKFLOW_STATUS: "running",
            INTERMEDIATE_OUTPUTS: {
                "research_orchestrator": {
                    "strategy": all_sub_answers[0]["retrieval_strategy"] if all_sub_answers else "N/A",
                    "context_length": sum(len(a["answer"]) for a in all_sub_answers),
                    "validation_passed": any(ans.get("is_relevant") for ans in all_sub_answers),
                    "total_sub_queries": total_queries,
                    "successful_queries": successful_queries,
                    "average_validation_score": avg_validation_score
                }
            }
        }