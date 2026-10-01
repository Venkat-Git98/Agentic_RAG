"""
Research Orchestrator Agent for LangGraph workflow.

For every sub-question in the research plan:
  1. retrieve the most relevant code sections with the hybrid retriever
     (explicit section/table references + vector search over the graph);
  2. check once, with a small model, that the retrieved text can answer the question;
  3. only if it cannot, fall back to a web search scoped to the Virginia code.

Sub-questions run in parallel. Each sub-answer carries the real sections it was
built from, so the synthesis step and the run trace show actual sources.
"""

import asyncio
import contextvars
import time
from typing import Dict, Any, List

from .base_agent import BaseLangGraphAgent
from core.state import AgentState
from state_keys import (
    USER_QUERY, RESEARCH_PLAN, SUB_QUERY_ANSWERS,
    CURRENT_STEP, WORKFLOW_STATUS, INTERMEDIATE_OUTPUTS,
)

from config import USE_PARALLEL_EXECUTION
from thinking_agents.thinking_validation_agent import ThinkingValidationAgent
from tools import retriever
from tools.web_search_tool import TavilySearchTool

# Which step produced a sub-query's context. A ContextVar keeps parallel sub-queries separate.
_RETRIEVAL_METHOD = contextvars.ContextVar("retrieval_method", default=None)

TOP_K = 5
WEB_SEARCH_SCOPE = "Virginia Uniform Statewide Building Code (Virginia Construction Code): "


class ResearchOrchestrator(BaseLangGraphAgent):
    """Retrieves and validates code context for each sub-question of the plan."""

    def __init__(self, llm=None):
        super().__init__(model_tier="tier_1", agent_name="ResearchOrchestrator")
        self.thinking_validation_agent = ThinkingValidationAgent()
        self.web_search_tool = TavilySearchTool()
        self.llm = llm or self.model
        mode = "PARALLEL" if USE_PARALLEL_EXECUTION else "SEQUENTIAL"
        self.logger.info(f"Research Orchestrator initialized with {mode} research workflow")

    async def execute(self, state: AgentState) -> Dict[str, Any]:
        """Runs research for every sub-query in the plan (or the user query when there is no plan)."""
        research_plan = state.get(RESEARCH_PLAN, [])
        if not research_plan:
            self.logger.warning("Research orchestrator called without a research plan. Using original query.")
            research_plan = [{"sub_query": state.get(USER_QUERY, "")}]

        sub_queries = [item.get("sub_query") for item in research_plan if item.get("sub_query")]
        total = len(sub_queries)
        started = time.time()
        try:
            if USE_PARALLEL_EXECUTION and total > 1:
                self.logger.info(f"Starting PARALLEL research for {total} sub-queries.")
                results = await asyncio.gather(
                    *(self._process_sub_query(q, i, total) for i, q in enumerate(sub_queries)),
                    return_exceptions=True)
            else:
                self.logger.info(f"Starting SEQUENTIAL research for {total} sub-queries.")
                results = [await self._process_sub_query(q, i, total) for i, q in enumerate(sub_queries)]
        except Exception as e:
            self.logger.error(f"Error in research orchestration: {e}", exc_info=True)
            return {
                "error_state": {"agent": self.agent_name, "error_type": type(e).__name__,
                                "error_message": str(e), "timestamp": "now"},
                CURRENT_STEP: "error",
                WORKFLOW_STATUS: "failed",
            }

        answers = [self._error_answer(q, r) if isinstance(r, Exception) else r for q, r in zip(sub_queries, results)]
        self.logger.info(f"--- Research phase complete in {time.time() - started:.2f}s. {len(answers)} sub-answers. ---")
        return self._format_final_research_output(answers)

    async def _process_sub_query(self, sub_query: str, index: int, total: int) -> Dict[str, Any]:
        started = time.time()
        _RETRIEVAL_METHOD.set(None)
        self.logger.info(f"--- Processing sub-query {index + 1}/{total}: '{sub_query[:100]}' ---")
        try:
            # The retriever is synchronous (database + embedding calls); keep it off the event loop.
            hits = await asyncio.to_thread(retriever.search, sub_query, TOP_K)
            context = retriever.format_context(hits)
            sources = [hit.label for hit in hits]
            if hits:
                _RETRIEVAL_METHOD.set(self._method(hits))
                validation = await self._validate_context_quality(sub_query, context)
            else:
                validation = {"is_relevant": False, "confidence_score": 0.0,
                              "reasoning": "Nothing relevant was found in the code graph."}

            if not validation.get("is_relevant", False):
                self.logger.info(f"Sub-query {index + 1}: code context not sufficient. Falling back to web search.")
                web_context = await self._web_search(sub_query)
                if web_context:
                    context, sources = web_context, ["Web search"]
                    _RETRIEVAL_METHOD.set("web search")

            self.logger.info(f"--- Sub-query {index + 1} completed in {time.time() - started:.2f}s ---")
            return {
                "sub_query": sub_query,
                "answer": context,
                "sources_used": sources,
                "retrieval_strategy": "hybrid",
                "retrieval_method": _RETRIEVAL_METHOD.get() or "hybrid",
                "validation_score": validation.get("confidence_score", 0.0),
                "is_relevant": validation.get("is_relevant", False),
                "reasoning": validation.get("reasoning", "No reasoning provided"),
            }
        except Exception as e:
            self.logger.error(f"Error processing sub-query {index + 1}: {e}", exc_info=True)
            return self._error_answer(sub_query, e)

    @staticmethod
    def _method(hits: List["retriever.Hit"]) -> str:
        """Names the signal that found the top result, for the run trace."""
        via = hits[0].via
        if "reference" in via:
            return "section lookup"
        return "vector search" if "vector" in via else "keyword search"

    @staticmethod
    def _error_answer(sub_query: str, error: Exception) -> Dict[str, Any]:
        return {
            "sub_query": sub_query,
            "answer": f"Error processing sub-query: {error}",
            "sources_used": [],
            "retrieval_strategy": "error",
            "validation_score": 0.0,
            "is_relevant": False,
            "reasoning": f"Exception occurred: {error}",
        }

    async def _validate_context_quality(self, query: str, context: str) -> Dict[str, Any]:
        """One relevance check of the retrieved context (score >= 6 of 10 counts as relevant)."""
        try:
            result = await self.thinking_validation_agent.execute({"query": query, "context": context})
            validation = result.get("validation_result", {"relevance_score": 1, "reasoning": "No validation result"})
            score = validation.get("relevance_score", 1)
            return {
                "is_relevant": score >= 6,
                "relevance_score": score,
                "reasoning": validation.get("reasoning", "No reasoning provided"),
                "confidence_score": score / 10.0,
            }
        except Exception as e:
            # A failed check must not throw away good code text and send the question to the web.
            self.logger.warning(f"ThinkingValidationAgent failed: {e}. Keeping the retrieved context.")
            return {"is_relevant": True, "confidence_score": 0.5, "reasoning": "Validation unavailable."}

    async def _web_search(self, query: str) -> str:
        """Web search, scoped to the Virginia code. Returns '' when it fails."""
        try:
            result = await asyncio.to_thread(self.web_search_tool, WEB_SEARCH_SCOPE + query)
            if isinstance(result, dict):
                if result.get("retrieval_method") == "web_search_error":
                    return ""
                return result.get("answer", "")
            return str(result)
        except Exception as e:
            self.logger.error(f"Web search fallback failed: {e}", exc_info=True)
            return ""

    def _format_final_research_output(self, all_sub_answers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Format the final research output for LangGraph state update."""
        successful_queries = sum(1 for ans in all_sub_answers if ans.get("is_relevant"))
        total_queries = len(all_sub_answers)
        avg_validation_score = sum(ans.get("validation_score", 0.0) for ans in all_sub_answers) / total_queries if total_queries > 0 else 0.0
        strategy = all_sub_answers[0]["retrieval_strategy"] if all_sub_answers else "N/A"

        return {
            SUB_QUERY_ANSWERS: all_sub_answers,
            "research_context": "\n\n---\n\n".join([a["answer"] for a in all_sub_answers]),
            "validation_reasoning": "\n\n---\n\n".join([a.get("reasoning", "No reasoning") for a in all_sub_answers]),
            "retrieval_strategy_used": strategy,
            "research_quality_score": avg_validation_score,
            CURRENT_STEP: "synthesis",
            WORKFLOW_STATUS: "running",
            INTERMEDIATE_OUTPUTS: {
                "research_orchestrator": {
                    "strategy": strategy,
                    "context_length": sum(len(a["answer"]) for a in all_sub_answers),
                    "validation_passed": any(ans.get("is_relevant") for ans in all_sub_answers),
                    "total_sub_queries": total_queries,
                    "successful_queries": successful_queries,
                    "average_validation_score": avg_validation_score
                }
            }
        }
