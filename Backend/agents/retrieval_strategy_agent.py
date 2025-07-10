"""
New, specialized agent to determine the best retrieval strategy for a given sub-query.
Enhanced with mathematical content awareness and enhanced Neo4j query prioritization.
"""
import json
import re
from typing import Dict, Any, Literal, Optional

from .base_agent import BaseLangGraphAgent
from state import AgentState
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
import logging
from langchain.chains.llm import LLMChain

from prompts import RETRIEVAL_STRATEGY_PROMPT

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class RetrievalStrategy(BaseModel):
    """
    The component that decides the retrieval strategy.
    Enhanced with mathematical content awareness.
    """
    strategy: Literal["direct_retrieval", "enhanced_retrieval", "vector_search", "keyword_search"] = Field(
        description="The selected retrieval strategy, with enhanced_retrieval for mathematical content."
    )
    confidence_score: float = Field(
        description="A score from 0.0 to 1.0 indicating the confidence in the chosen strategy."
    )
    reasoning: str = Field(
        description="The reasoning behind the chosen retrieval strategy."
    )
    mathematical_priority: bool = Field(
        default=False,
        description="Whether mathematical content was prioritized in strategy selection."
    )

class RetrievalStrategyAgent(BaseLangGraphAgent):
    """
    Agent that determines the optimal retrieval strategy for a given query.
    Enhanced with mathematical content awareness and enhanced Neo4j query prioritization.
    """

    def __init__(self):
        """Initialize the Retrieval Strategy Agent with Tier 2 model and mathematical awareness."""
        super().__init__(model_tier="tier_2", agent_name="RetrievalStrategyAgent")
        self.logger.info("Enhanced Retrieval Strategy Agent initialized with mathematical awareness")

    async def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        Determines the best retrieval strategy for the user's query with mathematical content awareness.
        Prioritizes enhanced Neo4j queries when mathematical content is detected.
        """
        query = state.get('query', '') or state.get('current_sub_query', '')
        
        # Enhanced state handling for mathematical content
        mathematical_analysis = state.get('mathematical_analysis', {})
        has_mathematical_content = state.get('has_mathematical_content', False)
        
        if not query:
            self.logger.error("No query found in state for retrieval strategy.")
            return {"error_state": {"agent": self.agent_name, "error_message": "Missing query"}}

        self.logger.info(f"Determining retrieval strategy for query: '{query[:100]}'")
        
        # Log mathematical content detection
        if has_mathematical_content:
            eq_count = len(mathematical_analysis.get('equation_references', []))
            table_count = len(mathematical_analysis.get('table_references', []))
            section_count = len(mathematical_analysis.get('context_sections', []))
            self.logger.info(f"Mathematical content detected: {eq_count} equations, {table_count} tables, {section_count} sections")

        try:
            # Apply mathematical content prioritization logic
            if has_mathematical_content:
                return await self._handle_mathematical_content_strategy(query, mathematical_analysis)
            else:
                return await self._handle_standard_strategy(query)
            
        except Exception as e:
            self.logger.error(f"Error determining retrieval strategy: {e}")
            # Re-raise the exception so orchestrator can handle fallback
            raise e

    async def _handle_mathematical_content_strategy(self, query: str, mathematical_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle strategy selection when mathematical content is detected.
        Prioritizes enhanced Neo4j queries for better mathematical content retrieval.
        """
        equation_refs = mathematical_analysis.get('equation_references', [])
        table_refs = mathematical_analysis.get('table_references', [])
        context_sections = mathematical_analysis.get('context_sections', [])
        
        # Priority 1: Direct section references detected - use enhanced retrieval
        if context_sections:
            section_id = context_sections[0]  # Use the first detected section
            self.logger.info(f"Using enhanced retrieval for section: {section_id}")
            return {
                "strategy": {
                    "tool": "direct_subsection_lookup",
                    "query": section_id,
                    "enhanced_mode": True,
                    "mathematical_priority": True
                },
                "retrieval_strategy": "enhanced_retrieval",
                "mathematical_enhancement": {
                    "prioritized": True,
                    "section_id": section_id,
                    "equation_count": len(equation_refs),
                    "table_count": len(table_refs)
                }
            }
        
        # Priority 2: Equation or table references - use enhanced keyword search
        if equation_refs or table_refs:
            enhanced_query = query
            
            # Build enhanced search terms
            search_terms = []
            for eq_ref in equation_refs:
                search_terms.append(eq_ref["reference"])
            for table_ref in table_refs:
                search_terms.append(table_ref["reference"])
            
            if search_terms:
                enhanced_query = f"{query} {' '.join(search_terms)}"
            
            self.logger.info(f"Using enhanced keyword search for mathematical content: {search_terms}")
            return {
                "strategy": {
                    "tool": "keyword_retrieval",
                    "query": enhanced_query,
                    "enhanced_mode": True,
                    "mathematical_priority": True
                },
                "retrieval_strategy": "enhanced_keyword_search",
                "mathematical_enhancement": {
                    "prioritized": True,
                    "search_terms": search_terms,
                    "equation_count": len(equation_refs),
                    "table_count": len(table_refs)
                }
            }
        
        # Priority 3: Mathematical content detected but no specific references - enhanced vector search
        self.logger.info("Mathematical content detected, using enhanced vector search")
        return {
            "strategy": {
                "tool": "vector_search",
                "query": query,
                "enhanced_mode": True,
                "mathematical_priority": True
            },
            "retrieval_strategy": "enhanced_vector_search",
            "mathematical_enhancement": {
                "prioritized": True,
                "mode": "enhanced_embedding"
            }
        }

    async def _handle_standard_strategy(self, query: str) -> Dict[str, Any]:
        """
        Handle strategy selection for non-mathematical content using the standard LLM-based approach.
        """
        # Enhanced prompt that includes mathematical awareness
        ENHANCED_RETRIEVAL_STRATEGY_PROMPT = """
You are a retrieval strategy expert for a building code AI with enhanced mathematical content capabilities.
Your task is to select the single best retrieval strategy for the given user query.

**Available Strategies:**

1.  **`direct_retrieval`**: Use this for queries that contain a specific section or subsection number (e.g., "1607.1", "Chapter 5", "Section 101.2"). This is the fastest and most precise method for targeted lookups.

2.  **`keyword_search`**: Use this for queries that contain unique, specific technical terms, proper nouns, or phrases that are likely to have an exact match in the text (e.g., "fire-retardant-treated wood", "ASTM E119", "cross-laminated timber").

3.  **`vector_search`**: Use this for all other queries, especially conceptual or descriptive questions that rely on semantic meaning rather than exact keywords (e.g., "What is the intent of the egress code?", "summarize the requirements for accessibility").

**Enhanced Decision Process:**
1.  Examine the user query for section numbers. If present, choose `direct_retrieval`.
2.  If no section number, look for unique, technical keywords. If present, choose `keyword_search`.
3.  Otherwise, default to `vector_search`.
4.  Consider the query's intent: is it asking for specific facts (keyword) or conceptual understanding (vector)?

**User Query:**
"{query}"

**Your JSON Response:**
Respond with a single, valid JSON object with three keys:
- "strategy": One of ["direct_retrieval", "vector_search", "keyword_search"]
- "confidence_score": A score from 0.0 to 1.0 indicating the confidence in the chosen strategy.
- "reasoning": A brief explanation for your choice.
"""

        try:
            prompt = ChatPromptTemplate.from_template(ENHANCED_RETRIEVAL_STRATEGY_PROMPT)
            chain = prompt | self.model
            
            response_ai_message = await chain.ainvoke({"query": query})
            response_text = response_ai_message.content
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not json_match:
                self.logger.warning("No JSON found in LLM response, defaulting to vector_search")
                return {"strategy": {"tool": "vector_search", "query": query}, "retrieval_strategy": "vector_search"}
            
            strategy_data = json.loads(json_match.group(0))
            strategy = strategy_data.get("strategy", "vector_search")
            confidence = strategy_data.get("confidence_score", 0.7)
            reasoning = strategy_data.get("reasoning", "Standard strategy selection")
            
            # Validate strategy
            valid_strategies = ["direct_retrieval", "vector_search", "keyword_search"]
            if strategy not in valid_strategies:
                self.logger.warning(f"Invalid strategy '{strategy}', defaulting to vector_search")
                strategy = "vector_search"
            
            # Map strategy to tool
            strategy_tool_map = {
                "direct_retrieval": "direct_subsection_lookup",
                "keyword_search": "keyword_retrieval", 
                "vector_search": "vector_search"
            }
            
            tool = strategy_tool_map.get(strategy, "vector_search")
            
            self.logger.info(f"LLM selected retrieval strategy: {strategy} (confidence: {confidence:.2f})")
            
            return {
                "strategy": {
                    "tool": tool,
                    "query": query,
                    "enhanced_mode": False,
                    "mathematical_priority": False
                },
                "retrieval_strategy": strategy,
                "confidence_score": confidence,
                "reasoning": reasoning
            }
            
        except Exception as e:
            self.logger.error(f"Error in standard strategy selection: {e}")
            # Fallback to vector search
            return {
                "strategy": {"tool": "vector_search", "query": query},
                "retrieval_strategy": "vector_search"
            } 