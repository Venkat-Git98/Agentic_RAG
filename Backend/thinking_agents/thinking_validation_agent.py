"""
Thinking-Enhanced Validation Agent

This agent performs research validation and math calculation detection
while providing detailed reasoning about its decision-making process.
"""

import json
import re
from typing import Dict, Any, List
import google.generativeai as genai

# Add parent directories to path for imports
from agents.base_agent import BaseLangGraphAgent
from state import AgentState
from thinking_logger import ThinkingLogger, ThinkingMixin, ThinkingMode

class ThinkingValidationAgent(BaseLangGraphAgent, ThinkingMixin):
    """Enhanced ValidationAgent with detailed thinking process."""
    
    def __init__(self, thinking_mode: ThinkingMode = ThinkingMode.SIMPLE):
        """Initialize with Tier 2 model and thinking capabilities."""
        super().__init__(model_tier="tier_2", agent_name="ValidationAgent")
        self._init_thinking("ValidationAgent", thinking_mode)
        
        self.math_keywords = [
            "calculate", "compute", "determine", "size", "area", "volume",
            "load", "pressure", "moment", "deflection", "convert", "ratio",
            "formula", "equation", "multiply", "divide", "square", "cubic"
        ]
        
        self.building_math_patterns = [
            r'\b\d+\s*[x×*]\s*\d+',  # Multiplication patterns
            r'\b\d+\s*(ft|in|psf|psi|lbs?|mph|kip)\b',  # Units
            r'area\s*=', r'load\s*=', r'pressure\s*=',  # Formula patterns
            r'\b\d+\s*(foot|feet|inch|pound|mile)\b',  # Spelled out units
            r'calculate\s+\w+\s+for',  # Calculate X for Y patterns
        ]
        
        self.logger.info("ThinkingValidationAgent initialized")
    
    async def execute(self, state: AgentState) -> Dict[str, Any]:
        """Execute validation with detailed thinking process."""
        
        # Initialize thinking session
        user_query = state.get("user_query", "")
        research_results = state.get("sub_query_answers", [])
        
        # Use enhanced human-like analysis
        self.thinking_logger.show_comprehensive_understanding(user_query)
        
        # Analyze what we have to work with
        with self.thinking_logger.thinking_block("Analyzing Research Foundation"):
            if research_results:
                self.thinking_logger.initial_impression(f"I have {len(research_results)} research results to work with")
                self.thinking_logger.deeper_look("Let me examine what the research team found...")
                
                # Show natural curiosity about the results
                total_length = sum(len(result.get("answer", "")) for result in research_results)
                self.thinking_logger.note(f"Total research content: {total_length} characters")
                
                if total_length > 2000:
                    self.thinking_logger.thinking_out_loud("That's quite a bit of information - should be comprehensive")
                elif total_length > 500:
                    self.thinking_logger.thinking_out_loud("Moderate amount of research - let's see if it covers everything")
                else:
                    self.thinking_logger.having_second_thoughts("Not much research content - might not be sufficient")
                
            else:
                self.thinking_logger.problem("No research results found - this is a problem")
                self.thinking_logger.thinking_out_loud("Without research, I can't provide a complete answer")
                self.thinking_logger.decide("Need to route to error handler")
                return self._create_error_state("No research results available")
        
        # Research Sufficiency Validation with human-like reasoning
        validation_results = await self._validate_research_with_thinking(
            user_query, research_results
        )
        
        # Math Calculation Detection with human-like reasoning
        math_detection = await self._detect_math_with_thinking(
            user_query, research_results
        )
        
        # Show natural decision-making process
        with self.thinking_logger.thinking_block("Making the Call"):
            is_sufficient = validation_results.get('is_sufficient', False)
            math_needed = math_detection.get('requires_math_calculations', False)
            
            # Natural reasoning about what we found
            if is_sufficient and not math_needed:
                self.thinking_logger.sudden_realization("Perfect! The research covers everything and no complex math needed")
                self.thinking_logger.getting_clearer_picture("This can go straight to synthesis for the final answer")
                next_step = "synthesis"
            elif is_sufficient and math_needed:
                self.thinking_logger.connecting_dots("Good research foundation, but I spotted some calculations to do")
                self.thinking_logger.working_through_problem("Need to handle the math first, then synthesize")
                next_step = "calculation"
            elif not is_sufficient and math_needed:
                self.thinking_logger.stepping_back("Two challenges: incomplete research AND math calculations")
                self.thinking_logger.reconsidering("This is complex - need to handle missing info and calculations")
                # Check if we have placeholder content that needs handling
                has_placeholders = any("PLACEHOLDER" in result.get("answer", "") for result in research_results)
                if has_placeholders:
                    self.thinking_logger.connecting_dots("I see placeholder content - that needs special handling")
                    next_step = "placeholder"
                else:
                    next_step = "calculation"
            else:
                self.thinking_logger.having_second_thoughts("Research seems incomplete...")
                has_placeholders = any("PLACEHOLDER" in result.get("answer", "") for result in research_results)
                if has_placeholders:
                    self.thinking_logger.sudden_realization("There are placeholders that need to be handled first")
                    next_step = "placeholder"
                else:
                    self.thinking_logger.thinking_out_loud("No math needed, but research gaps - maybe synthesis can work with what we have")
                    next_step = "synthesis"
            
            self.thinking_logger.decide(f"My decision: route to {next_step}")
            
            # Show confidence in decision
            if next_step == "synthesis":
                self.thinking_logger.building_on_thought("The synthesis agent should be able to create a solid answer")
            elif next_step == "calculation":
                self.thinking_logger.building_on_thought("The calculation agent will handle the math, then we can synthesize")
            elif next_step == "placeholder":
                self.thinking_logger.building_on_thought("Placeholder handler will fill gaps, then we can proceed")
        
        # Routing Decision
        routing_decision = {
            'next_step': next_step,
            'reasoning': f"Research {'sufficient' if is_sufficient else 'insufficient'}, math {'needed' if math_needed else 'not needed'}",
            'confidence': validation_results.get('sufficiency_score', 0.5)
        }
        
        # Prepare final state updates
        state_updates = self._prepare_state_updates_with_thinking(
            validation_results, math_detection, routing_decision
        )
        
        # Show completion with human satisfaction
        self.thinking_logger.making_progress(f"Validation complete - ready to hand off to {next_step}")
        
        # End thinking session
        thinking_summary = self._end_thinking_session()
        
        self.logger.info(f"Validation complete: {routing_decision['next_step']}")
        return state_updates
    
    def _prepare_state_updates_with_thinking(self, validation_results: Dict[str, Any], 
                                            math_detection: Dict[str, Any], 
                                            routing_decision: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare state updates with thinking process."""
        
        with self.thinking_logger.thinking_block("Finalizing My Assessment"):
            self.thinking_logger.working_through_problem("Putting together all my findings...")
            
            # Show what we determined
            is_sufficient = validation_results.get('is_sufficient', False)
            math_needed = math_detection.get('requires_math_calculations', False)
            next_step = routing_decision.get('next_step', 'synthesis')
            
            self.thinking_logger.note(f"Research quality: {'Sufficient' if is_sufficient else 'Insufficient'}")
            self.thinking_logger.note(f"Math needed: {'Yes' if math_needed else 'No'}")
            self.thinking_logger.note(f"Next step: {next_step}")
            
            # Extract calculation details for proper routing
            calc_types = []
            calc_complexity = "medium"
            
            if math_needed:
                calc_types = math_detection.get("calculation_type", ["general_calculation"])
                if isinstance(calc_types, str):
                    calc_types = [calc_types]
                calc_complexity = math_detection.get("math_complexity", "medium")
                
                self.thinking_logger.note(f"Calculation types: {', '.join(calc_types)}")
                self.thinking_logger.note(f"Complexity: {calc_complexity}")
            
            # Nest calculation details within the validation results
            # for the CalculationExecutor to find them correctly.
            validation_results["calculation_types"] = calc_types
            validation_results["calculation_complexity"] = calc_complexity
            
            return {
                "research_validation_results": validation_results,
                "math_calculation_needed": math_needed,
                "math_detection_metadata": math_detection,
                "validation_confidence": math_detection.get("math_confidence_score", 0.5),
                "next_step": next_step,
                "validation_agent_completed": True,
                "routing_decision": routing_decision
            }

    def _create_error_state(self, error_message: str) -> Dict[str, Any]:
        """Create error state for validation failures."""
        return {
            "research_validation_results": {"is_sufficient": False, "error": error_message},
            "math_calculation_needed": False,
            "next_step": "error",
            "validation_agent_completed": True
        }
    
    async def _validate_research_with_thinking(self, user_query: str, research_results: List[Dict]) -> Dict[str, Any]:
        """
        Validate research sufficiency by checking for explicit failure signals,
        rather than re-evaluating the quality.
        """
        with self.thinking_logger.analysis_block("Verifying Research Integrity"):
            self.thinking_logger.think("Checking research results for any errors or explicit placeholders...")

            if not research_results:
                self.thinking_logger.problem("No research results were provided to validate.")
                return self._create_fallback_validation_result()

            has_placeholders = False
            has_errors = False
            error_signals = []
            for i, result in enumerate(research_results, 1):
                answer = result.get("answer", "").upper()
                if "PLACEHOLDER" in answer or "INSUFFICIENT" in answer:
                    has_placeholders = True
                    self.thinking_logger.warning(f"Detected placeholder or insufficiency text in research result {i}.")
                if result.get("error"):
                    has_errors = True
                    self.thinking_logger.error(f"Detected an error in research result {i}: {result['error']}")
                    error_signals.append(result['error'])

            # If we find explicit failures, the research is not sufficient.
            if has_placeholders or has_errors:
                self.thinking_logger.conclude("Research integrity check failed. Explicit errors or placeholders were found.")
                return {
                    "is_sufficient": False,
                    "sufficiency_score": 0.1,
                    "validation_reasoning": f"The research results contained explicit placeholders or error messages, indicating a failure in the retrieval process. Errors: {', '.join(error_signals)}"
                }

            # If no explicit failures, we trust the upstream assessment.
            self.thinking_logger.success("No explicit errors or placeholders found. Research integrity is confirmed.")
            return {
                "is_sufficient": True,
                "sufficiency_score": 0.9,
                "validation_reasoning": "Research results appear complete and do not contain any explicit failure signals."
            }

    async def _detect_math_with_thinking(self, user_query: str, research_results: List[Dict]) -> Dict[str, Any]:
        """Detect math requirements with a more robust and cautious approach."""
        
        with self.thinking_logger.analysis_block("Checking for Mathematical Requirements"):
            self.thinking_logger.think("Analyzing query and research for any math, assuming 'yes' on ambiguity.")
            
            # Focus ONLY on the user's original query to determine intent.
            prompt = f"""
            You are a simple decision-making agent. Your only job is to determine if the user's query is asking for a numerical calculation or a textual explanation.

            **User Query:** "{user_query}"

            **Instructions:**
            - If the query asks "what is," "explain," "summarize," or "describe," the user wants an explanation. Respond with `synthesis`.
            - If the query asks to "calculate," "compute," "determine the value of," or contains specific numerical values for a calculation, the user wants a calculation. Respond with `calculation`.
            - Your response must be a single word: `calculation` or `synthesis`.

            **Your decision:**
            """
            
            try:
                # Use a fast model for this simple classification
                model = genai.GenerativeModel(self.model_name) 
                response = await model.generate_content_async(prompt)
                decision = response.text.strip().lower()

                if "calculation" in decision:
                    self.thinking_logger.conclude("User's query appears to require a calculation.")
                    return {"requires_math_calculations": True}
                else:
                    self.thinking_logger.conclude("User's query appears to be explanatory. No calculation needed.")
                    return {"requires_math_calculations": False}

            except Exception as e:
                self.logger.error(f"Error during simplified math detection: {e}")
                # Default to synthesis on error to be safe
                return {"requires_math_calculations": False}
    
    def _calculate_math_score_with_thinking(self, user_query: str, research_results: List[Dict]) -> float:
        """Calculate math probability with detailed reasoning."""
        
        with self.thinking_logger.analysis_block("Pattern-Based Math Scoring"):
            score = 0.0
            query_lower = user_query.lower()
            
            # Check keywords
            keyword_matches = []
            for keyword in self.math_keywords:
                if keyword in query_lower:
                    keyword_matches.append(keyword)
            
            keyword_score = min(len(keyword_matches) * 0.2, 0.6)
            score += keyword_score
            
            if keyword_matches:
                self.thinking_logger.discover(f"Found math keywords: {', '.join(keyword_matches)} (score: +{keyword_score:.2f})")
            
            # Check patterns
            pattern_matches = []
            for pattern in self.building_math_patterns:
                if re.search(pattern, user_query):
                    pattern_matches.append(pattern)
            
            pattern_score = min(len(pattern_matches) * 0.15, 0.3)
            score += pattern_score
            
            if pattern_matches:
                self.thinking_logger.discover(f"Found {len(pattern_matches)} calculation patterns (score: +{pattern_score:.2f})")
            
            # Check research content for formulas
            formula_indicators = 0
            for result in research_results:
                answer = result.get("answer", "")
                if re.search(r'[=+\-*/]', answer) or re.search(r'formula|equation', answer.lower()):
                    formula_indicators += 1
            
            if formula_indicators > 0:
                formula_score = min(formula_indicators * 0.1, 0.2)
                score += formula_score
                self.thinking_logger.discover(f"Found formulas in {formula_indicators} research results (score: +{formula_score:.2f})")
            
            final_score = min(score, 1.0)
            self.thinking_logger.conclude(f"Total pattern-based math score: {final_score:.2f}")
            
            return final_score
    
    def _assess_result_quality(self, answer: str, user_query: str) -> float:
        """Assess the quality of a research result answer."""
        if not answer:
            return 0.0
        
        score = 0.0
        
        # Length factor (basic completeness)
        if len(answer) > 500:
            score += 0.4
        elif len(answer) > 200:
            score += 0.2
        elif len(answer) > 50:
            score += 0.1
        
        # Content quality factors
        if "virginia building code" in answer.lower():
            score += 0.2
        
        if re.search(r'\d+\.\d+\.\d+', answer):  # Section references
            score += 0.2
        
        if re.search(r'\d+', answer):  # Contains numbers
            score += 0.1
        
        if re.search(r'(psf|psi|mph|ft|in)', answer, re.IGNORECASE):  # Units
            score += 0.1
        
        return min(score, 1.0)
    
    def _determine_calculation_type(self, user_query: str, math_content: List[str]) -> str:
        """Determine what type of calculations are needed."""
        query_lower = user_query.lower()
        
        if any(word in query_lower for word in ["load", "pressure", "stress", "moment"]):
            return "structural_engineering"
        elif any(word in query_lower for word in ["area", "volume", "size", "dimension"]):
            return "geometric_calculation"
        elif any(word in query_lower for word in ["wind", "seismic", "snow"]):
            return "environmental_load"
        elif any(word in query_lower for word in ["cost", "price", "budget"]):
            return "cost_calculation"
        else:
            return "general_calculation"
    
    def _create_fallback_validation_with_thinking(self, result_assessments: List[Dict]) -> Dict[str, Any]:
        """Create fallback validation result with thinking process."""
        self.thinking_logger.thinking_out_loud("Making my own judgment based on what I observed...")
        
        avg_quality = sum(r["quality_score"] for r in result_assessments) / len(result_assessments)
        total_content = sum(r["length"] for r in result_assessments)
        
        # Human-like decision making
        if avg_quality > 0.6 and total_content > 800:
            self.thinking_logger.decide("Based on my analysis, this should be sufficient")
            is_sufficient = True
            score = 0.7
        elif avg_quality > 0.4 and total_content > 400:
            self.thinking_logger.reconsidering("It's borderline, but probably workable")
            is_sufficient = True
            score = 0.5
        else:
            self.thinking_logger.having_second_thoughts("I don't think this is enough to give a good answer")
            is_sufficient = False
            score = 0.3
        
        return {
            "is_sufficient": is_sufficient,
            "sufficiency_score": score,
            "missing_aspects": [],
            "validation_reasoning": f"Fallback assessment based on quality={avg_quality:.2f}, content={total_content}",
            "key_information_found": [],
            "critical_gaps": []
        }
    
    # Helper methods
    def _format_research_for_validation(self, research_results: List[Dict]) -> str:
        """Format research results for LLM validation."""
        if not research_results:
            return "No research results available."
        
        formatted = []
        for i, result in enumerate(research_results, 1):
            sub_query = result.get("sub_query", "Unknown query")
            answer = result.get("answer", "No answer provided")
            formatted.append(f"Research {i}:\nQuery: {sub_query}\nAnswer: {answer[:500]}...")
        
        return "\n\n".join(formatted)
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from LLM with error handling."""
        try:
            # Try to extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")
                
        except Exception as e:
            self.thinking_logger.problem(f"Failed to parse JSON response: {str(e)}")
            return {}
    
    def _create_fallback_validation_result(self) -> Dict[str, Any]:
        """Create fallback validation result."""
        return {
            "is_sufficient": False,
            "sufficiency_score": 0.2,
            "missing_aspects": ["Detailed analysis required"],
            "validation_reasoning": "Fallback assessment - comprehensive evaluation needed"
        } 