"""
Triage Agent for LangGraph workflow.

This agent performs the initial classification of user queries to determine
the appropriate routing through the workflow. It's a lightweight agent that
makes quick decisions about query type and complexity.
"""

import os
import json
import re
from typing import Dict, Any

# Add parent directories to path for imports
from .base_agent import BaseLangGraphAgent
from state import AgentState

class TriageAgent(BaseLangGraphAgent):
    """
    Triage Agent for initial query classification.
    
    This agent quickly classifies incoming queries to determine the best
    processing path through the workflow. It uses lightweight classification
    to avoid unnecessary processing for simple queries.
    """
    
    def __init__(self):
        """Initialize the Triage Agent with Tier 2 model for fast classification."""
        super().__init__(model_tier="tier_2", agent_name="TriageAgent")
        
        # Classification criteria
        self.direct_retrieval_patterns = [
            r"show me section\s+[\d\.]+",
            r"what is section\s+[\d\.]+",
            r"explain section\s+[\d\.]+",
            r"show me table\s+[\d\.]+",
            r"what is table\s+[\d\.]+",
            r"summarize chapter\s+\d+",
            r"what is chapter\s+\d+",
        ]
        
        self.clarification_patterns = [
            r"^what\s*$",
            r"^tell me about.*code.*$",
            r"^help.*$",
            r"^explain.*$"  # Only if very vague
        ]
        
        self.rejection_patterns = [
            r".*weather.*",
            r".*sports.*",
            r".*entertainment.*",
            r".*politics.*",
            r".*recipes.*"
        ]
    
    async def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute the triage classification logic.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dictionary containing classification results
        """
        user_query = state["user_query"].strip()
        context_payload = state.get("context_payload", "")
        
        self.logger.info(f"Triaging query: {user_query[:100]}...")
        
        # Quick pattern-based pre-screening
        quick_classification = self._quick_pattern_screening(user_query)
        
        if quick_classification:
            self.logger.info(f"Quick classification: {quick_classification}")
            return {
                "triage_classification": quick_classification,
                "triage_reasoning": f"Pattern-based classification: {quick_classification}",
                "triage_confidence": 0.9,
                "current_step": "planning",
                "workflow_status": "running"
            }
        
        # Use LLM for more complex classification
        llm_classification = await self._llm_classification(user_query, context_payload)
        
        self.logger.info(f"LLM classification: {llm_classification['classification']}")
        
        return {
            "triage_classification": llm_classification["classification"],
            "triage_reasoning": llm_classification["reasoning"],
            "triage_confidence": llm_classification.get("confidence", 0.8),
            "current_step": "planning",
            "workflow_status": "running"
        }
    
    def _quick_pattern_screening(self, query: str) -> str:
        """
        Performs quick pattern-based screening for obvious cases.
        
        Args:
            query: User query string
            
        Returns:
            Classification if pattern matches, None otherwise
        """
        query_lower = query.lower().strip()
        
        # Check for rejection patterns
        for pattern in self.rejection_patterns:
            if re.search(pattern, query_lower, re.IGNORECASE):
                return "reject"
        
        # Check for direct retrieval patterns
        for pattern in self.direct_retrieval_patterns:
            if re.search(pattern, query_lower, re.IGNORECASE):
                return "direct_retrieval"
        
        # Check for clarification patterns (very basic queries)
        if len(query.split()) <= 3:
            for pattern in self.clarification_patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    return "clarify"
        
        return None
    
    async def _llm_classification(self, query: str, context_payload: str) -> Dict[str, Any]:
        """
        Uses LLM for sophisticated query classification.
        
        Args:
            query: User query string
            context_payload: Context from conversation manager
            
        Returns:
            Dictionary with classification, reasoning, and confidence
        """
        prompt = f"""
You are a query classification specialist for a Virginia Building Code AI system.
Your task is to quickly classify the user's query into one of four categories.

**Classification Options:**
1. "engage" - Complex queries requiring research across multiple code sections
2. "direct_retrieval" - Simple requests for specific, identifiable entities
3. "clarify" - Vague queries that need more information
4. "reject" - Off-topic or inappropriate queries

**Query Analysis Guidelines:**

**Direct Retrieval Patterns:**
- "Show me Section X.X.X" 
- "What is Table X.X.X?"
- "Explain Chapter X"
- "What does Section X say about..."

**Engage Patterns:**
- "What are the requirements for..."
- "How do I calculate..."
- "What's the difference between..."
- "Compare X and Y..."
- Questions requiring multi-step reasoning

**Clarify Patterns:**
- Very vague: "Tell me about codes"
- Incomplete: "What about structural?"
- Ambiguous: "Help with building"

**Reject Patterns:**
- Non-building-code topics
- Legal advice requests
- Other jurisdictions' codes

**Context:**
{context_payload[:500] if context_payload else "No previous context"}

**User Query:**
{query}

**Your Response (JSON only):**
{{
    "classification": "engage|direct_retrieval|clarify|reject",
    "reasoning": "Brief explanation of your decision",
    "confidence": 0.0-1.0
}}
"""
        
        try:
            response_text = await self.generate_content_async(prompt)
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not json_match:
                self.logger.warning("No JSON found in LLM response, defaulting to engage")
                return {
                    "classification": "engage",
                    "reasoning": "Failed to parse LLM response, defaulting to engage for safety",
                    "confidence": 0.5
                }
            
            result = json.loads(json_match.group(0))
            
            # Validate classification
            valid_classifications = ["engage", "direct_retrieval", "clarify", "reject"]
            if result.get("classification") not in valid_classifications:
                self.logger.warning(f"Invalid classification {result.get('classification')}, defaulting to engage")
                result["classification"] = "engage"
                result["reasoning"] = "Invalid classification detected, defaulting to engage"
                result["confidence"] = 0.5
            
            return result
            
        except (json.JSONDecodeError, Exception) as e:
            self.logger.error(f"Error in LLM classification: {e}")
            return {
                "classification": "engage",
                "reasoning": f"Classification error: {str(e)}, defaulting to engage",
                "confidence": 0.5
            }
    
    def _validate_agent_specific_state(self, state: AgentState) -> None:
        """
        Validates triage agent specific state requirements.
        
        Args:
            state: State to validate
            
        Raises:
            ValueError: If required fields are missing
        """
        if not state.get("user_query"):
            raise ValueError("user_query is required for triage")
        
        if state.get("current_step") != "triage":
            self.logger.warning(f"Expected current_step='triage', got '{state.get('current_step')}'")
    
    def _apply_agent_specific_updates(self, state: AgentState, output_data: Dict[str, Any]) -> AgentState:
        """
        Applies triage-specific state updates.
        
        Args:
            state: Current state
            output_data: Triage output data
            
        Returns:
            Updated state
        """
        updated_state = state.copy()
        
        # Set next step based on classification
        classification = output_data.get("triage_classification")
        
        if classification in ["clarify", "reject"]:
            # These classifications end the workflow immediately
            updated_state["current_step"] = "finish"
            updated_state["workflow_status"] = "completed"
            # Set a direct answer for these cases
            if classification == "clarify":
                updated_state["direct_answer"] = "I need more information to help you. Could you please provide more specific details about what you're looking for in the Virginia Building Code?"
            else:  # reject
                updated_state["direct_answer"] = "I can only help with questions related to the Virginia Building Code. Your query appears to be outside my area of expertise."
        else:
            # Continue to planning for engage and direct_retrieval
            updated_state["current_step"] = "planning"
            updated_state["workflow_status"] = "running"
        
        return updated_state 