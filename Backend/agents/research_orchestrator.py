"""
Research Orchestrator Agent for LangGraph workflow.

This agent integrates the sophisticated parallel research logic from the original
ParallelResearchTool, preserving all advanced features including:
- Parallel sub-query processing
- HyDE document generation
- Semantic reranking
- Equation detection and mathematical content
- Multi-tier fallback systems (Vector → Graph → Keyword → Web)
- Advanced context enhancement and table formatting
"""

import asyncio
import json
from typing import Dict, Any, List
import hashlib

# Add parent directories to path for imports
from .base_agent import BaseLangGraphAgent
from state import AgentState

# Import the original research tool logic
from tools.parallel_research_tool import ParallelResearchTool
from tools.web_search_tool import TavilySearchTool
from tools.keyword_retrieval_tool import KeywordRetrievalTool
from tools.reranker import Reranker
from config import USE_RERANKER, redis_client
from prompts import RE_PLANNING_PROMPT

class ResearchOrchestrator(BaseLangGraphAgent):
    """
    Research Orchestrator Agent for sophisticated parallel research execution.
    
    This agent leverages the existing ParallelResearchTool implementation while
    adapting it to the LangGraph workflow. It preserves all advanced features:
    - Parallel processing of multiple sub-queries
    - HyDE document embedding and retrieval
    - Semantic reranking with cross-encoder models
    - Mathematical content processing and equation detection
    - Multi-tier fallback chains for comprehensive coverage
    - Advanced table formatting and context enhancement
    """
    
    def __init__(self):
        """Initialize the Research Orchestrator with Tier 2 model for coordination."""
        super().__init__(model_tier="tier_2", agent_name="ResearchOrchestrator")
        
        # Initialize the original research tool
        self.research_tool = ParallelResearchTool()
        
        # Initialize supporting tools
        self.web_search_tool = TavilySearchTool()
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
        
        self.logger.info("Research Orchestrator initialized with all tools")
    
    async def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute the parallel research using the new strategy-based approach.
        """
        research_plan = state.get("research_plan", [])
        original_query = state.get("user_query", "")
        
        if not research_plan:
            self.logger.error("No research plan provided to research orchestrator")
            return {"sub_answers": []} # Return empty list to avoid crash
        
        self.logger.info(f"Executing research for {len(research_plan)} sub-queries.")

        # --- Sub-Query Cache Logic ---
        cached_sub_answers = []
        queries_to_run = []
        if redis_client:
            for task in research_plan:
                sub_query = task.get('sub_query') or task.get('query')
                if not sub_query: continue
                try:
                    query_hash = hashlib.sha256(sub_query.encode()).hexdigest()
                    cache_key = f"sub_cache:{query_hash}"
                    cached_result = redis_client.get(cache_key)
                    if cached_result:
                        self.logger.info(f"--- [SUB-QUERY CACHE HIT] for: {sub_query[:100]}... ---")
                        cached_sub_answers.append(json.loads(cached_result))
                    else:
                        queries_to_run.append(task)
                except Exception as e:
                    self.logger.error(f"Sub-query cache check failed for '{sub_query[:100]}': {e}")
                    queries_to_run.append(task)
            
            self.logger.info(f"Sub-query cache summary: {len(cached_sub_answers)} hits, {len(queries_to_run)} misses.")
        else:
            queries_to_run = research_plan
        # --- End Cache Logic ---
        
        newly_generated_answers = []
        if queries_to_run:
            # Use the simplified, strategy-driven research tool
            research_results = await self.research_tool._run_async_logic(queries_to_run, original_query)
            newly_generated_answers = research_results.get("sub_answers", [])

            # --- Save new results to Sub-Query Cache ---
            if redis_client:
                for answer in newly_generated_answers:
                    sub_query = answer.get('sub_query')
                    if not sub_query: continue
                    try:
                        query_hash = hashlib.sha256(sub_query.encode()).hexdigest()
                        cache_key = f"sub_cache:{query_hash}"
                        redis_client.set(cache_key, json.dumps(answer), ex=3600) # Cache for 1 hour
                        self.logger.info(f"--- [SAVED TO SUB-CACHE] for: {sub_query[:100]}... ---")
                    except Exception as e:
                        self.logger.error(f"Sub-query cache save failed for '{sub_query[:100]}': {e}")
            # --- End Cache Save Logic ---

        final_answers = cached_sub_answers + newly_generated_answers
        
        self.logger.info(f"Research completed: {len(final_answers)} sub-answers generated")
        
        # CRITICAL FIX: Restore metadata and quality score calculations with robust defaults.
        metadata = self._extract_research_metadata(final_answers)
        quality_scores = self._calculate_quality_scores(final_answers)
        
        return {
            "sub_query_answers": final_answers,
            "research_metadata": metadata,
            "retrieval_quality_scores": quality_scores
        }
    
    async def _execute_parallel_research(self, research_plan: List[Dict[str, str]], original_query: str) -> Dict[str, Any]:
        """
        Executes the parallel research using the original tool logic.
        
        Args:
            research_plan: List of sub-query plans with hyde documents
            original_query: Original user query for context
            
        Returns:
            Research results from the parallel research tool
        """
        # The original tool expects synchronous execution, so we wrap it
        loop = asyncio.get_event_loop()
        
        # Execute in thread pool to avoid blocking
        research_results = await loop.run_in_executor(
            None,
            self.research_tool,
            research_plan,
            original_query
        )
        
        return research_results
    
    async def _process_research_results(self, research_results: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """
        Processes the results from the parallel research tool and formats for LangGraph.
        
        Args:
            research_results: Results from the parallel research tool
            state: Current workflow state
            
        Returns:
            Formatted research output for state update
        """
        sub_answers = research_results.get("sub_answers", [])
        
        if not sub_answers:
            self.logger.warning("No sub-answers generated by research tool")
            return {
                "research_results": research_results,
                "sub_query_answers": [],
                "research_metadata": {
                    "total_sub_queries": 0,
                    "successful_queries": 0,
                    "fallback_methods_used": []
                },
                "current_step": "synthesis",
                "workflow_status": "running"
            }
        
        # Extract metadata for quality tracking
        metadata = self._extract_research_metadata(sub_answers)
        
        # Calculate quality scores
        quality_scores = self._calculate_quality_scores(sub_answers)
        
        self.logger.info(f"Research completed: {len(sub_answers)} sub-answers generated")
        
        return {
            "research_results": research_results,
            "sub_query_answers": sub_answers,
            "research_metadata": metadata,
            "retrieval_quality_scores": quality_scores,
            "parallel_execution_log": metadata.get("execution_log", []),
            "current_step": "synthesis",
            "workflow_status": "running"
        }
    
    def _extract_research_metadata(self, sub_answers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extracts comprehensive metadata from a list of sub-answers."""
        if not sub_answers:
            return {
                "total_sub_queries": 0, "successful_queries": 0, "failed_queries": 0,
                "retrieval_methods_used": [], "total_sources": 0
            }

        retrieval_methods = [ans.get("retrieval_method", "unknown") for ans in sub_answers]
        successful_queries = len([a for a in sub_answers if "No information was found" not in a.get("answer", "")])

        return {
            "total_sub_queries": len(sub_answers),
            "successful_queries": successful_queries,
            "failed_queries": len(sub_answers) - successful_queries,
            "retrieval_methods_used": list(set(retrieval_methods)),
            "total_sources": len(sub_answers) # Simplified for now
        }
    
    def _calculate_quality_scores(self, sub_answers: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculates quality scores based on the research results."""
        if not sub_answers:
            return {"overall_quality": 0.0, "answer_completeness": 0.0}

        completeness = len([a for a in sub_answers if "No information was found" not in a.get("answer", "")]) / len(sub_answers)
        
        # Simple quality score based on completeness
        quality = completeness * 0.9 # Base score on whether answers were found

        return {
            "overall_quality": round(quality, 2),
            "answer_completeness": round(completeness, 2)
        }
    
    def _validate_agent_specific_state(self, state: AgentState) -> None:
        """
        Validates research agent specific state requirements.
        
        Args:
            state: State to validate
            
        Raises:
            ValueError: If required fields are missing
        """
        if not state.get("research_plan"):
            raise ValueError("research_plan is required for research orchestrator")
        
        if state.get("current_step") not in ["research", "planning"]:
            self.logger.warning(f"Unexpected current_step '{state.get('current_step')}' for research orchestrator")
    
    def _apply_agent_specific_updates(self, state: AgentState, output_data: Dict[str, Any]) -> AgentState:
        """
        Applies research-specific state updates.
        
        Args:
            state: Current state
            output_data: Research output data
            
        Returns:
            Updated state
        """
        updated_state = state.copy()
        
        # Store research metadata for debugging
        if updated_state.get("intermediate_outputs") is not None:
            research_metadata = output_data.get("research_metadata", {})
            quality_scores = output_data.get("retrieval_quality_scores", {})
            
            updated_state["intermediate_outputs"]["research_details"] = {
                "total_sub_queries": research_metadata.get("total_sub_queries", 0),
                "successful_queries": research_metadata.get("successful_queries", 0),
                "fallback_methods": research_metadata.get("fallback_methods_used", []),
                "overall_quality": quality_scores.get("overall_quality", 0.0),
                "source_diversity": research_metadata.get("source_diversity", 0)
            }
        
        # Set overall quality metrics
        quality_scores = output_data.get("retrieval_quality_scores", {})
        if quality_scores.get("overall_quality"):
            updated_state["confidence_score"] = quality_scores["overall_quality"]
        
        # Update quality metrics
        if updated_state.get("quality_metrics") is None:
            updated_state["quality_metrics"] = {
                "context_sufficiency_score": 0.0,
                "retrieval_relevance_score": 0.0,
                "synthesis_quality_score": 0.0,
                "total_sources_used": 0,
                "fallback_methods_used": []
            }
        
        updated_state["quality_metrics"]["retrieval_relevance_score"] = quality_scores.get("overall_quality", 0.0)
        updated_state["quality_metrics"]["total_sources_used"] = output_data.get("research_metadata", {}).get("total_sources", 0)
        updated_state["quality_metrics"]["fallback_methods_used"] = output_data.get("research_metadata", {}).get("fallback_methods_used", [])
        
        return updated_state

    async def _handle_insufficient_context(self, sub_query: str, original_query: str) -> Dict[str, Any]:
        """
        Handles cases where initial context is insufficient by re-planning.
        """
        self.logger.warning(f"Initial context for sub-query '{sub_query[:100]}...' was insufficient. Initiating re-planning.")
        
        prompt = RE_PLANNING_PROMPT.format(sub_query=sub_query, original_query=original_query)
        
        try:
            response_text = await self.generate_content_async(prompt)
            re_plan_data = json.loads(response_text)
            
            tool_to_use = re_plan_data.get("tool_to_use")
            search_query = re_plan_data.get("search_query")
            
            self.logger.info(f"Re-planning decided to use '{tool_to_use}' with query: '{search_query}'")
            
            if tool_to_use == "keyword_retrieval":
                return self.keyword_tool(query=search_query)
            elif tool_to_use == "deep_graph_retrieval":
                # Assuming a graph retrieval tool exists and is implemented
                # This is a placeholder for the actual deep graph retrieval logic
                self.logger.warning("Deep graph retrieval is not fully implemented yet.")
                return {"answer": "Deep graph retrieval not implemented."}
            elif tool_to_use == "web_search":
                return self.web_search_tool(query=search_query)
            else:
                self.logger.error(f"Unknown tool recommended by re-planning: {tool_to_use}")
                return {"answer": "Re-planning failed to select a valid tool."}
                
        except Exception as e:
            self.logger.error(f"Error during re-planning: {e}", exc_info=True)
            # As a final fallback, use web search
            return self.web_search_tool(query=sub_query)

class EnhancedResearchOrchestrator(ResearchOrchestrator):
    """
    Enhanced Research Orchestrator with additional strategies for specialized query types.
    
    This version includes enhanced features for:
    - Equation detection and mathematical content processing
    - Table enhancement and formatting
    - Compliance-focused research strategies
    - Calculation-optimized research approaches
    """
    
    def __init__(self):
        """Initialize the Enhanced Research Orchestrator."""
        super().__init__()
        self.agent_name = "EnhancedResearchOrchestrator"
        self.logger.info("Enhanced Research Orchestrator initialized with specialized strategies")
        
        # Enhanced research strategies
        self.research_strategies = {
            "equation_focused": self._enhance_equation_research,
            "table_focused": self._enhance_table_research,
            "compliance_focused": self._enhance_compliance_research,
            "calculation_focused": self._enhance_calculation_research
        }
    
    async def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        Enhanced execution with strategy-based research optimization.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dictionary containing enhanced research results
        """
        # Check if we can apply enhanced strategies
        enhanced_plan = await self._apply_enhanced_strategies(state)
        if enhanced_plan:
            # Update the research plan with enhanced strategies
            updated_state = state.copy()
            updated_state["research_plan"] = enhanced_plan
            return await super().execute(updated_state)
        
        # Fall back to original research logic
        return await super().execute(state)
    
    async def _apply_enhanced_strategies(self, state: AgentState) -> List[Dict[str, str]]:
        """
        Applies enhanced research strategies based on query analysis.
        
        Args:
            state: Current workflow state
            
        Returns:
            Enhanced research plan if applicable, None otherwise
        """
        research_plan = state.get("research_plan", [])
        original_query = state.get("original_query", "").lower()
        
        # Check for equation-focused queries
        if any(word in original_query for word in ["equation", "formula", "calculate"]):
            return await self._enhance_equation_research(research_plan, state)
        
        # Check for table-focused queries
        if any(word in original_query for word in ["table", "chart", "values"]):
            return await self._enhance_table_research(research_plan, state)
        
        # Check for compliance-focused queries
        if any(word in original_query for word in ["comply", "requirement", "shall", "must"]):
            return await self._enhance_compliance_research(research_plan, state)
        
        return None
    
    async def _enhance_equation_research(self, research_plan: List[Dict[str, str]], state: AgentState) -> List[Dict[str, str]]:
        """Enhances research plan for equation-focused queries."""
        enhanced_plan = research_plan.copy()
        
        # Add specific equation retrieval sub-query
        enhanced_plan.append({
            "sub_query": f"Mathematical equations and formulas related to: {state['original_query']}",
            "hyde_document": "Building code equations include mathematical expressions with variables, coefficients, and calculation procedures. Formulas are typically presented with variable definitions and applicable conditions."
        })
        
        return enhanced_plan
    
    async def _enhance_table_research(self, research_plan: List[Dict[str, str]], state: AgentState) -> List[Dict[str, str]]:
        """Enhances research plan for table-focused queries."""
        enhanced_plan = research_plan.copy()
        
        # Add specific table retrieval sub-query
        enhanced_plan.append({
            "sub_query": f"Tables, charts, and tabulated data for: {state['original_query']}",
            "hyde_document": "Building code tables provide organized data including load values, material properties, dimensional requirements, and regulatory limits presented in structured format."
        })
        
        return enhanced_plan
    
    async def _enhance_compliance_research(self, research_plan: List[Dict[str, str]], state: AgentState) -> List[Dict[str, str]]:
        """Enhances research plan for compliance-focused queries."""
        enhanced_plan = research_plan.copy()
        
        # Add specific compliance requirements sub-query
        enhanced_plan.append({
            "sub_query": f"Compliance requirements and regulatory criteria for: {state['original_query']}",
            "hyde_document": "Building code compliance involves meeting specific requirements, following prescribed procedures, and satisfying regulatory criteria as mandated by the Virginia Building Code."
        })
        
        return enhanced_plan
    
    async def _enhance_calculation_research(self, research_plan: List[Dict[str, str]], state: AgentState) -> List[Dict[str, str]]:
        """Enhances research plan for calculation-focused queries."""
        enhanced_plan = research_plan.copy()
        
        # Add specific calculation and methodology sub-query
        enhanced_plan.append({
            "sub_query": f"Calculation procedures, step-by-step methods, and worked examples for: {state['original_query']}",
            "hyde_document": "Building code calculations involve specific procedures, step-by-step methodologies, variable definitions, and worked examples demonstrating proper application of formulas and equations."
        })
        
        return enhanced_plan