"""
Synthesis Agent for the LangGraph workflow.

This agent synthesizes the final answer from multiple sub-query answers.
Enhanced with cross-user query caching storage.
"""

import logging
import hashlib
import json
from datetime import datetime
from typing import Dict, Any, List

from .base_agent import BaseLangGraphAgent
from core.state import AgentState
from state_keys import (
    USER_QUERY, SUB_QUERY_ANSWERS, FINAL_ANSWER, SYNTHESIS_METADATA,
    SOURCE_CITATIONS, CONFIDENCE_SCORE, CURRENT_STEP, INTERMEDIATE_OUTPUTS
)
from tools.synthesis_tool import SynthesisTool
from prompts import CALCULATION_SYNTHESIS_PROMPT
from config import redis_client


class SynthesisAgent(BaseLangGraphAgent):
    """
    Synthesis Agent responsible for generating the final answer from research results.
    Enhanced with query caching storage for cross-user answer reuse.
    """
    
    def __init__(self):
        """Initialize the Synthesis Agent."""
        super().__init__(model_tier="tier_1", agent_name="SynthesisAgent")
        self.synthesis_tool = SynthesisTool()
        self.logger.info("Synthesis Agent initialized successfully")
    
    async def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute the synthesis process.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dictionary containing the final answer and metadata
        """
        self.logger.info(f"Synthesizing final answer from {len(state.get(SUB_QUERY_ANSWERS, []))} sub-answers for original query: '{state.get(USER_QUERY, '')[:100]}'")
        
        try:
            # Execute synthesis
            synthesis_result = await self._execute_synthesis(
                original_query=state[USER_QUERY],
                current_query=state[USER_QUERY],
                sub_query_answers=state.get(SUB_QUERY_ANSWERS, [])
            )
            
            # Process the synthesis result
            result = await self._process_synthesis_result(synthesis_result, state)
            
            # 🔥 NEW: Store successful answer in query cache for future reuse
            await self._store_query_cache(state.get(USER_QUERY, ""), result, state)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in synthesis execution: {e}", exc_info=True)
            return {
                FINAL_ANSWER: f"I apologize, but I encountered an error while synthesizing the final answer: {str(e)}",
                SYNTHESIS_METADATA: {"error": str(e)},
                SOURCE_CITATIONS: [],
                CONFIDENCE_SCORE: 0.0
            }
    
    async def _execute_synthesis(self, original_query: str, current_query: str, sub_query_answers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute the synthesis using the synthesis tool.
        
        Args:
            original_query: The original user query
            current_query: The current query (usually same as original)
            sub_query_answers: List of sub-query answers
            
        Returns:
            Dictionary containing the synthesis result
        """
        return self.synthesis_tool(
            original_query=original_query,
            current_query=current_query,
            sub_answers=sub_query_answers
        )
    
    async def _process_synthesis_result(self, synthesis_result: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """
        Process the synthesis result and create the final output.
        
        Args:
            synthesis_result: Result from synthesis tool
            state: Current workflow state
            
        Returns:
            Dictionary containing processed synthesis output
        """
        final_answer = synthesis_result.get("final_answer", "")
        sub_query_answers = state.get(SUB_QUERY_ANSWERS, [])
        
        # Extract citations
        citations = self._extract_citations(final_answer, sub_query_answers)
        
        # Calculate synthesis metadata
        synthesis_metadata = self._calculate_synthesis_metadata(final_answer, sub_query_answers)
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(synthesis_metadata, state)
        
        self.logger.info(f"Synthesis completed: {len(final_answer)} characters, confidence: {confidence_score:.2f}")
        
        return {
            FINAL_ANSWER: final_answer,
            SYNTHESIS_METADATA: synthesis_metadata,
            SOURCE_CITATIONS: citations,
            CONFIDENCE_SCORE: confidence_score
        }
    
    async def _store_query_cache(self, user_query: str, synthesis_result: Dict[str, Any], state: AgentState):
        """
        Store the successful query-answer pair in Redis cache for cross-user reuse.
        Only stores high-quality answers that meet caching criteria.
        
        Args:
            user_query: Original user query
            synthesis_result: Successful synthesis result  
            state: Current workflow state
        """
        if not redis_client or not user_query.strip():
            return
            
        try:
            final_answer = synthesis_result.get(FINAL_ANSWER, "")
            confidence_score = synthesis_result.get(CONFIDENCE_SCORE, 0.0)
            
            # 🎯 Relaxed Cache Quality Criteria
            should_cache = (
                len(final_answer) > 15 and  # Answer should have some substance
                confidence_score >= 0.5 and  # Medium confidence is acceptable for caching
                not state.get("cache_hit", False) and
                not state.get("error_state")
            )
            
            if not should_cache:
                self.logger.info(f"Answer does not meet caching criteria. Length: {len(final_answer)}, Confidence: {confidence_score:.2f}")
                return
            
            # Create cache entry
            query_hash = hashlib.sha256(user_query.lower().strip().encode()).hexdigest()
            cache_key = f"query_cache:{query_hash}"
            
            cache_data = {
                "query": user_query.strip(),
                "answer": final_answer,
                "confidence_score": confidence_score,
                "sources": synthesis_result.get(SOURCE_CITATIONS, []),
                "synthesis_metadata": synthesis_result.get(SYNTHESIS_METADATA, {}),
                "cached_at": datetime.now().isoformat(),
                "usage_count": 0,
                "last_validated": datetime.now().isoformat()
            }
            
            # Store in Redis with expiration (optional - remove expiration for permanent cache)
            redis_client.set(cache_key, json.dumps(cache_data), ex=86400*30)  # 30 days expiration
            
            # Store usage tracking
            usage_key = f"{cache_key}:usage"
            redis_client.set(usage_key, 0)
            
            self.logger.info(f"✅ Stored high-quality answer in query cache (confidence: {confidence_score:.2f})")
            
            # Track cache statistics
            redis_client.incr("query_cache:total_stored")
            
        except Exception as e:
            self.logger.error(f"Error storing query cache: {e}")
    
    def _extract_citations(self, final_answer: str, sub_query_answers: List[Dict[str, Any]]) -> List[str]:
        """
        Extract citations from the final answer and sub-query answers.
        
        Args:
            final_answer: The synthesized final answer
            sub_query_answers: List of sub-query answers
            
        Returns:
            List of unique citations
        """
        citations = set()
        
        # Extract citations from sub-query answers
        for answer in sub_query_answers:
            sources = answer.get("sources_used", [])
            if isinstance(sources, list):
                citations.update(sources)
        
        # Simple citation extraction from final answer
        import re
        section_refs = re.findall(r'Section\s+\d+\.?\d*\.?\d*', final_answer)
        citations.update(section_refs)
        
        return list(citations)
    
    def _calculate_synthesis_metadata(self, final_answer: str, sub_query_answers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate metadata about the synthesis process.
        
        Args:
            final_answer: The synthesized final answer
            sub_query_answers: List of sub-query answers
            
        Returns:
            Dictionary containing synthesis metadata
        """
        # Basic metrics
        answer_length = len(final_answer)
        word_count = len(final_answer.split())
        sub_answer_count = len(sub_query_answers)
        
        # Source integration metrics
        total_sources = sum(len(ans.get("sources_used", [])) for ans in sub_query_answers)
        unique_sources = len(set().union(*[ans.get("sources_used", []) for ans in sub_query_answers]))
        
        # Content integration metrics
        successful_integrations = len([ans for ans in sub_query_answers if ans.get("answer") and len(ans["answer"]) > 50])
        
        # Quality indicators
        has_citations = "[Source:" in final_answer or "Section" in final_answer
        has_structure = any(marker in final_answer for marker in ["1.", "2.", "•", "-", "**"])
        
        return {
            "answer_length_chars": answer_length,
            "answer_word_count": word_count,
            "sub_answers_integrated": sub_answer_count,
            "successful_integrations": successful_integrations,
            "total_sources_referenced": total_sources,
            "unique_sources_used": unique_sources,
            "has_proper_citations": has_citations,
            "has_structured_format": has_structure,
            "integration_rate": successful_integrations / sub_answer_count if sub_answer_count > 0 else 0.0,
            "source_diversity": unique_sources / total_sources if total_sources > 0 else 0.0
        }
    
    def _calculate_confidence_score(self, synthesis_metadata: Dict[str, Any], state: AgentState) -> float:
        """
        Calculates an overall confidence score for the synthesis.
        
        Args:
            synthesis_metadata: Metadata from synthesis process
            state: Current workflow state
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        # For now, we use a simple heuristic based on the number of sources
        # and whether any fallback methods were required.
        
        num_sources = len(synthesis_metadata.get("sources_used", []))
        
        # Start with a base score
        score = 0.5
        
        # Increase score for more sources
        if num_sources > 0:
            score += 0.1
        if num_sources > 2:
            score += 0.1
        if num_sources > 4:
            score += 0.1
        
        # Simple confidence calculation
        return min(1.0, score) # Cap at 1.0
    
    def _validate_agent_specific_state(self, state: AgentState) -> None:
        """
        Validates synthesis agent specific state requirements.
        
        Args:
            state: State to validate
            
        Raises:
            ValueError: If required fields are missing
        """
        if not state.get(SUB_QUERY_ANSWERS):
            raise ValueError("sub_query_answers is required for synthesis agent")
        
        if state.get(CURRENT_STEP) not in ["synthesis", "research"]:
            self.logger.warning(f"Unexpected current_step '{state.get(CURRENT_STEP)}' for synthesis agent")
    
    def _apply_agent_specific_updates(self, state: AgentState, output_data: Dict[str, Any]) -> AgentState:
        """
        Applies synthesis-specific updates to the state.
        
        This method ensures that intermediate outputs are correctly logged without
        overwriting previous logs from other agents.
        
        Args:
            state: The current state of the workflow.
            output_data: The output from the synthesis agent's execution.
            
        Returns:
            The updated state.
        """
        updated_state = state.copy()
        
        # Ensure intermediate_outputs is a list
        if "intermediate_outputs" not in updated_state or not isinstance(updated_state["intermediate_outputs"], list):
            updated_state["intermediate_outputs"] = []

        # Log the synthesis output
        log_entry = {
            "agent": self.agent_name,
            "output": {
                "final_answer_length": len(output_data.get(FINAL_ANSWER, "")),
                "confidence_score": output_data.get(CONFIDENCE_SCORE, 0.0),
                "citation_count": len(output_data.get(SOURCE_CITATIONS, []))
            },
            "timestamp": datetime.now().isoformat()
        }
        
        updated_state["intermediate_outputs"].append(log_entry)
        
        return updated_state

class EnhancedSynthesisAgent(SynthesisAgent):
    """
    Enhanced Synthesis Agent with specialized strategies for different
    query types (calculation, comparison, compliance).
    """
    
    def __init__(self):
        super().__init__()
        self.logger.info("Enhanced Synthesis Agent initialized with specialized strategies")

    async def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        Executes the synthesis logic, trying enhanced strategies first
        and falling back to the standard synthesis if needed.
        """
        # Try enhanced synthesis first
        enhanced_result = await self._try_enhanced_synthesis(state)
        
        if enhanced_result:
            return await self._process_synthesis_result(enhanced_result, state)
        
        # Fallback to standard synthesis
        self.logger.warning("No enhanced synthesis strategy applied. Falling back to standard synthesis.")
        return await super().execute(state)

    async def _try_enhanced_synthesis(self, state: AgentState) -> Dict[str, Any]:
        """Tries to apply an enhanced synthesis strategy based on the state."""
        if state.get("math_calculation_needed"):
            self.logger.info("🧮 Applying enhanced 'Calculation' synthesis strategy.")
            return await self._enhance_calculation_synthesis(state)
        
        # Other strategies can be added here
        # elif state.get("is_comparison_query"):
        #     return await self._enhance_comparison_synthesis(state)
        
        return None

    async def _enhance_calculation_synthesis(self, state: AgentState) -> Dict[str, Any]:
        """
        Enhanced synthesis for queries requiring calculations.
        Uses the specialized CALCULATION_SYNTHESIS_PROMPT to ensure mathematical calculations are performed.
        """
        user_query = state[USER_QUERY]
        sub_query_answers = state.get(SUB_QUERY_ANSWERS, [])

        # Construct the sub-answers string
        sub_answers_text = "".join([
            f"Sub-Query: {ans.get('sub_query', 'N/A')}\nAnswer: {ans.get('answer', 'N/A')}\n\n"
            for ans in sub_query_answers
        ])

        # Use the specialized calculation prompt
        prompt = CALCULATION_SYNTHESIS_PROMPT.format(
            original_user_query=user_query,
            sub_answers_text=sub_answers_text
        )
        
        self.logger.info("🧮 Executing calculation synthesis with enhanced mathematical instructions")
        response_text = await self.generate_content_async(prompt)
        
        return {"final_answer": response_text}