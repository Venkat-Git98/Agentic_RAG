"""
Thinking-Enhanced Placeholder Handler

This agent manages insufficient research scenarios while providing
detailed reasoning about gap analysis and enhancement planning.
"""

import sys
import os
import json
from typing import Dict, Any, List

# Add parent directories to path for imports
from agents.base_agent import BaseLangGraphAgent
from state import AgentState
from thinking_logger import ThinkingLogger, ThinkingMixin, ThinkingMode
from state_keys import (
    USER_QUERY, SUB_QUERY_ANSWERS
)

class ThinkingPlaceholderHandler(BaseLangGraphAgent, ThinkingMixin):
    """Enhanced PlaceholderHandler with detailed thinking process."""
    
    def __init__(self, thinking_mode: ThinkingMode = ThinkingMode.SIMPLE):
        """Initialize with Tier 2 model and thinking capabilities."""
        super().__init__(model_tier="tier_2", agent_name="PlaceholderHandler")
        self._init_thinking("PlaceholderHandler", thinking_mode)
        self.logger.info("ThinkingPlaceholderHandler initialized")
    
    async def execute(self, state: AgentState) -> Dict[str, Any]:
        """Execute placeholder handling with detailed thinking process."""
        
        # Extract necessary state info
        validation_results = state.get("research_validation_results", {})
        missing_aspects = state.get("missing_research_aspects", [])
        user_query = state.get(USER_QUERY, "")
        
        # Natural problem understanding
        self.thinking_logger.show_comprehensive_understanding(user_query)
        
        if missing_aspects:
            self.thinking_logger.discovering(f"Found {len(missing_aspects)} specific gaps: {', '.join(missing_aspects)}")
            self.thinking_logger.breaking_down("Need to provide partial answer and explain what additional research is needed")
        else:
            self.thinking_logger.discovering("Research gaps identified but not specifically categorized")
            self.thinking_logger.breaking_down("Need to analyze what information is missing and create partial response")
        
        # Create comprehensive placeholder context
        placeholder_context = await self._create_placeholder_context_with_thinking(
            user_query, validation_results, missing_aspects
        )
        
        # Generate partial answer with placeholders
        partial_answer = await self._generate_partial_answer_with_thinking(
            user_query, state, placeholder_context
        )
        
        # Prepare enhancement suggestions
        enhancement_suggestions = self._prepare_enhancement_suggestions_with_thinking(
            validation_results, missing_aspects
        )
        
        # Show natural conclusion
        self.thinking_logger.calculating_step("Preparing partial answer with clear placeholders for missing information")
        self.thinking_logger.concluding_answer("Created professional response explaining what we know and what needs additional research")
        
        # Prepare state updates
        state_updates = self._prepare_placeholder_state_updates_with_thinking(
            placeholder_context, partial_answer, enhancement_suggestions, state
        )
        
        # End thinking session
        thinking_summary = self._end_thinking_session()
        
        self.logger.info("Placeholder handling completed")
        return state_updates
    
    async def _create_placeholder_context_with_thinking(self, user_query: str, validation_results: Dict, missing_aspects: List[str]) -> Dict[str, Any]:
        """Create comprehensive placeholder context with thinking."""
        
        with self.thinking_logger.creative_process("Placeholder Context Creation"):
            self.thinking_logger.think("Analyzing research gaps to create structured placeholder context...")
            
            validation_reasoning = validation_results.get('validation_reasoning', 'No reasoning provided')
            sufficiency_score = validation_results.get('sufficiency_score', 0.0)
            
            self.thinking_logger.consider(f"Validation reasoning: {validation_reasoning}")
            self.thinking_logger.consider(f"Sufficiency score: {sufficiency_score:.2f}")
            
            context_prompt = f"""
            Create a placeholder context for an incomplete research scenario.

            USER QUERY: {user_query}
            
            VALIDATION RESULTS: {validation_reasoning}
            
            MISSING ASPECTS: {', '.join(missing_aspects) if missing_aspects else 'General insufficiency'}

            Create a JSON response with:
            {{
                "insufficiency_summary": "Clear explanation of what's missing",
                "available_information": "What research was found",
                "critical_gaps": ["gap1", "gap2"],
                "placeholder_sections": [
                    {{
                        "section_title": "Missing Section Title",
                        "placeholder_text": "[Placeholder: Additional research needed for ...]",
                        "required_research": "Specific research needed"
                    }}
                ],
                "enhancement_priority": "high|medium|low",
                "estimated_completion_effort": "Brief effort estimate"
            }}
            """
            
            self.thinking_logger.reason("Sending context creation request to LLM...")
            
            try:
                response = await self.generate_content_async(context_prompt)
                parsed_context = self._parse_json_response_with_thinking(response)
                
                # Validate the context
                if parsed_context and 'insufficiency_summary' in parsed_context:
                    self.thinking_logger.success("✅ Placeholder context created successfully")
                    
                    gaps = parsed_context.get('critical_gaps', [])
                    priority = parsed_context.get('enhancement_priority', 'medium')
                    
                    self.thinking_logger.discover(f"Identified {len(gaps)} critical gaps")
                    self.thinking_logger.note(f"Enhancement priority: {priority}")
                    
                    return parsed_context
                else:
                    self.thinking_logger.problem("❌ LLM response validation failed")
                    return self._create_fallback_placeholder_context_with_thinking(missing_aspects)
                    
            except Exception as e:
                self.thinking_logger.problem(f"LLM context creation failed: {str(e)}")
                self.thinking_logger.adapt("Falling back to template-based context creation")
                return self._create_fallback_placeholder_context_with_thinking(missing_aspects)
    
    async def _generate_partial_answer_with_thinking(self, user_query: str, state: AgentState, placeholder_context: Dict) -> str:
        """Generate partial answer with thinking process - NO MANUAL CALCULATIONS."""
        
        with self.thinking_logger.creative_process("Partial Answer Generation"):
            research_results = state.get(SUB_QUERY_ANSWERS, [])
            available_info = self._format_available_research_with_thinking(research_results)
            
            self.thinking_logger.think("Crafting professional partial answer with clear placeholders...")
            self.thinking_logger.consider(f"Available research: {len(research_results)} results")
            
            answer_prompt = f"""
            Generate a partial answer for insufficient research scenarios ONLY - DO NOT perform any mathematical calculations.

            USER QUERY: {user_query}
            
            AVAILABLE RESEARCH:
            {available_info}
            
            PLACEHOLDER CONTEXT:
            {json.dumps(placeholder_context, indent=2)}

            Generate a professional response that:
            1. Acknowledges the user's question
            2. Provides available research information clearly
            3. Uses clear placeholders for missing research information (NOT calculations)
            4. Explains what additional research is needed
            5. Maintains professional tone throughout
            
            CRITICAL: If the question involves calculations, state that calculations require Docker-based execution and should be handled by the CalculationExecutor.

            Format placeholders as: [PLACEHOLDER: Specific description of missing research information]
            """
            
            self.thinking_logger.reason("Generating partial answer with LLM...")
            
            try:
                response = await self.generate_content_async(answer_prompt)
                
                if response and len(response.strip()) > 50:
                    placeholder_count = response.count('[PLACEHOLDER:')
                    self.thinking_logger.success(f"✅ Generated partial answer with {placeholder_count} placeholders")
                    self.thinking_logger.review(f"Answer length: {len(response)} characters")
                    
                    return response.strip()
                else:
                    self.thinking_logger.problem("❌ Generated answer too short or empty")
                    return self._create_fallback_partial_answer_with_thinking(user_query, available_info)
                    
            except Exception as e:
                self.thinking_logger.problem(f"LLM answer generation failed: {str(e)}")
                self.thinking_logger.adapt("Creating template-based partial answer")
                return self._create_fallback_partial_answer_with_thinking(user_query, available_info)
    
    def _prepare_enhancement_suggestions_with_thinking(self, validation_results: Dict, missing_aspects: List[str]) -> Dict[str, Any]:
        """Prepare enhancement suggestions with thinking."""
        
        with self.thinking_logger.analysis_block("Enhancement Strategy Planning"):
            self.thinking_logger.think("Developing specific strategies for research enhancement...")
            
            suggestions = {
                "immediate_actions": [],
                "research_priorities": [],
                "specific_queries": [],
                "timeline_estimate": "To be determined"
            }
            
            # Process missing aspects
            for i, aspect in enumerate(missing_aspects, 1):
                self.thinking_logger.consider(f"Missing aspect {i}: {aspect}")
                
                suggestions["immediate_actions"].append({
                    "action": f"Research {aspect}",
                    "priority": "high",
                    "description": f"Conduct targeted research on {aspect}"
                })
                
                # Generate specific query suggestions
                query_suggestion = f"Find detailed information about {aspect} in Virginia Building Code"
                suggestions["specific_queries"].append(query_suggestion)
                
                self.thinking_logger.craft(f"Created action plan for: {aspect}")
            
            # Extract additional research needs from validation
            additional_research = validation_results.get("additional_research_needed", [])
            for research_item in additional_research:
                self.thinking_logger.note(f"Additional research needed: {research_item}")
                
                suggestions["research_priorities"].append({
                    "area": research_item,
                    "priority": "medium",
                    "expected_impact": "Improves answer completeness"
                })
            
            # Estimate timeline
            total_items = len(missing_aspects) + len(additional_research)
            if total_items <= 2:
                timeline = "1-2 hours"
            elif total_items <= 5:
                timeline = "3-5 hours"
            else:
                timeline = "6+ hours"
            
            suggestions["timeline_estimate"] = timeline
            
            self.thinking_logger.conclude(f"Enhancement strategy complete: {total_items} items, estimated {timeline}")
            
            return suggestions
    
    def _prepare_placeholder_state_updates_with_thinking(self, placeholder_context: Dict, partial_answer: str, 
                                                        enhancement_suggestions: Dict, state: AgentState) -> Dict[str, Any]:
        """Prepare final state updates with thinking process."""
        
        with self.thinking_logger.synthesis_block("Final State Preparation"):
            self.thinking_logger.think("Assembling final state update with placeholder information...")
            
            # Combine new partial answer with existing research
            original_answers = state.get(SUB_QUERY_ANSWERS, [])
            
            # Create a new sub-answer for the placeholder content
            placeholder_answer = {
                "sub_query": "Placeholder for Insufficient Research",
                "answer": partial_answer,
                "is_placeholder": True,
                "sources_used": []
            }
            
            # Append the new placeholder answer to the list
            updated_answers = original_answers + [placeholder_answer]
            
            self.thinking_logger.craft("Created consolidated answer list including new placeholder content")
            
            state_updates = {
                SUB_QUERY_ANSWERS: updated_answers,
                "placeholder_metadata": {
                    "context": placeholder_context,
                    "enhancement_suggestions": enhancement_suggestions,
                    "placeholders_generated": 1  # Simplified for now
                },
                "enhancement_triggered": True, # Flag for workflow
                "current_step": "synthesis"  # Move on to synthesis
            }
            
            self.thinking_logger.success("✅ State updates prepared successfully")
            
            return state_updates
            
    def _format_available_research_with_thinking(self, research_results: List[Dict]) -> str:
        """Format available research for the prompt, showing thinking."""
        
        with self.thinking_logger.analysis_block("Formatting Available Research"):
            
            if not research_results:
                self.thinking_logger.note("No research results to format.")
                return "No specific research information was found."
            
            formatted_texts = []
            for i, result in enumerate(research_results, 1):
                sub_query = result.get('sub_query', f'Result {i}')
                answer = result.get('answer', 'No answer provided.')
                
                # Skip placeholders in the available research context
                if "PLACEHOLDER:" in answer:
                    self.thinking_logger.note(f"Skipping placeholder content for sub-query: '{sub_query}'")
                    continue
                
                formatted_text = f"Sub-Query: {sub_query}\nAnswer: {answer}\n---"
                formatted_texts.append(formatted_text)
                
                self.thinking_logger.review(f"Formatted research item {i}: '{sub_query[:50]}...'")
            
            if not formatted_texts:
                self.thinking_logger.warning("All research results were placeholders; no available info.")
                return "All research conducted resulted in placeholders, indicating significant information gaps."
            
            return "\n".join(formatted_texts)
    
    def _parse_json_response_with_thinking(self, response: str) -> Dict[str, Any]:
        """Parse JSON response with detailed thinking process."""
        
        with self.thinking_logger.analysis_block("Parsing LLM JSON Response"):
            self.thinking_logger.think("Attempting to parse JSON from LLM response...")
            
            try:
                # Use a more robust method to find the JSON block
                first_brace = response.find('{')
                last_brace = response.rfind('}')
                
                if first_brace == -1 or last_brace == -1 or last_brace < first_brace:
                    raise json.JSONDecodeError("Could not find a valid JSON object.", response, 0)
                
                json_string = response[first_brace:last_brace+1]
                parsed_json = json.loads(json_string)
                
                self.thinking_logger.success("✅ JSON parsed successfully")
                self.thinking_logger.review(f"Parsed keys: {list(parsed_json.keys())}")
                
                return parsed_json
            
            except json.JSONDecodeError as e:
                self.thinking_logger.problem(f"JSON parsing failed: {e}")
                self.thinking_logger.review(f"Problematic response: {response[:200]}...")
                return None
    
    def _create_fallback_placeholder_context_with_thinking(self, missing_aspects: List[str]) -> Dict[str, Any]:
        """Create fallback placeholder context with thinking."""
        
        with self.thinking_logger.adapt_block("Creating Fallback Context"):
            self.thinking_logger.think("LLM context creation failed. Building fallback context from template.")
            
            return {
                "insufficiency_summary": "Research was insufficient to provide a complete answer.",
                "critical_gaps": missing_aspects or ["general information"],
                "enhancement_priority": "high"
            }
            
    def _create_fallback_partial_answer_with_thinking(self, user_query: str, available_info: str) -> str:
        """Create fallback partial answer with thinking."""
        
        with self.thinking_logger.adapt_block("Creating Fallback Partial Answer"):
            self.thinking_logger.think("LLM partial answer generation failed. Using template.")
            
            return f"""
            Regarding your query about "{user_query}", I was able to find the following information:
            
            {available_info}
            
            [PLACEHOLDER: Additional research is required to provide a complete and comprehensive answer.]
            """ 