"""
Thinking-Enhanced Validation Agent

This agent performs research validation and math calculation detection
while providing detailed reasoning about its decision-making process.
"""

import json
import re
from typing import Dict, Any, List, Literal, Optional
import google.generativeai as genai

from agents.base_agent import BaseLangGraphAgent
from state import AgentState
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
import logging
from langchain.chains.llm import LLMChain

from prompts import QUALITY_CHECK_PROMPT

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ValidationResult(BaseModel):
    """
    The result of the validation, including a score and reasoning.
    """
    relevance_score: int = Field(
        description="A score from 1 (not relevant) to 10 (highly relevant) indicating the context's relevance to the query."
    )
    reasoning: str = Field(
        description="A brief justification for the relevance score."
    )

class ThinkingValidationAgent(BaseLangGraphAgent):
    """
    Agent that validates the relevance and quality of retrieved context.
    """
    
    def __init__(self):
        """Initialize the Thinking Validation Agent with Tier 2 model."""
        super().__init__(model_tier="tier_2", agent_name="ThinkingValidationAgent")
        self.logger.info("Thinking Validation Agent initialized")
    
    async def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        Validates the relevance of the retrieved context.
        """
        query = state.get('query', '')
        context = state.get('context', '')
        
        if not query or not context:
            self.logger.error(f"Missing query or context for validation. Query: {bool(query)}, Context: {bool(context)}")
            return {
                "error_state": {
                    "agent": self.agent_name,
                    "error_type": "MissingData",
                    "error_message": "Missing query or context for validation",
                    "timestamp": "now"
                }
            }
        
        self.logger.info(f"Validating context for query: '{query[:100]}'")

        try:
            # Escape backslashes and quotes in context to prevent JSON parsing issues
            escaped_context = context.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')
            escaped_query = query.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')
            
            # Use raw prompt + JSON parsing instead of structured output to avoid Gemini compatibility issues
            prompt = ChatPromptTemplate.from_template(QUALITY_CHECK_PROMPT.template)
            chain = prompt | self.model

            # Invoke the chain with the escaped query and context
            response_ai_message = await chain.ainvoke({"sub_query": escaped_query, "context_str": escaped_context})
            response_text = response_ai_message.content

            # Extract JSON from response with better error handling
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not json_match:
                self.logger.warning("No JSON found in LLM response, defaulting to neutral score")
                return {
                    "validation_result": {
                        "relevance_score": 5,
                        "reasoning": "Could not parse LLM response, defaulting to neutral"
                    }
                }
            
            json_str = json_match.group(0)
            
            # Try to fix common JSON escape issues before parsing
            try:
                validation_data = json.loads(json_str)
            except json.JSONDecodeError as json_error:
                self.logger.warning(f"Initial JSON parse failed: {json_error}. Attempting to fix escape issues.")
                # Try to fix common escape issues
                fixed_json = json_str.replace('\\', '\\\\')  # Double escape backslashes
                fixed_json = re.sub(r'(?<!\\)"', '\\"', fixed_json)  # Escape unescaped quotes
                try:
                    validation_data = json.loads(fixed_json)
                except json.JSONDecodeError as second_error:
                    self.logger.error(f"Could not fix JSON: {second_error}. Using fallback.")
                    return {
                        "validation_result": {
                            "relevance_score": 5,
                            "reasoning": f"JSON parsing error: {second_error}"
                        }
                    }
            
            # Validate and ensure required fields
            relevance_score = validation_data.get("relevance_score", 5)
            reasoning = validation_data.get("reasoning", "No reasoning provided")
            
            # Ensure score is in valid range
            if not isinstance(relevance_score, int) or relevance_score < 1 or relevance_score > 10:
                relevance_score = 5
            
            result = {
                "relevance_score": relevance_score,
                "reasoning": reasoning
            }
            
            self.logger.info(f"Validation result: {result}")
            return {"validation_result": result}
                
        except Exception as e:
            self.logger.error(f"Error during context validation: {e}")
            # Fallback to a neutral validation result in case of error
            return {
                "validation_result": {
                    "relevance_score": 5,
                    "reasoning": f"Defaulted due to error: {e}"
                }
            } 