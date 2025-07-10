"""
Base agent class for LangGraph-based agents.

This module provides the foundational structure for all agents in the
LangGraph workflow, including common utilities, logging, and execution patterns.
"""

import sys
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
import time
from datetime import datetime
import google.generativeai as genai
import hashlib
from langgraph_agentic_ai.config import redis_client

# Add parent directories to path for imports
from config import TIER_1_MODEL_NAME, TIER_2_MODEL_NAME, GOOGLE_API_KEY
from state import AgentState, log_agent_execution

# Use the LangChain wrapper for Google Generative AI
from langchain_google_genai import ChatGoogleGenerativeAI

# Configure Gemini if not already configured
if GOOGLE_API_KEY:
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
    except Exception as e:
        pass  # Already configured or other issue

class BaseLangGraphAgent(ABC):
    """
    Abstract base class for all agents in the LangGraph workflow.
    """
    
    def __init__(self, model_tier: str = "tier_2", agent_name: Optional[str] = None):
        """
        Initializes the agent with a specific model tier and name.
        
        Args:
            model_tier: "tier_1" for high-capability model (e.g., Gemini Pro 1.5),
                        "tier_2" for faster, cost-effective model (e.g., Gemini Flash 1.5)
            agent_name: A descriptive name for the agent.
        """
        self.agent_name = agent_name or self.__class__.__name__
        self.logger = logging.getLogger(self.__class__.__name__)

        # Use ChatGoogleGenerativeAI for LangChain compatibility
        model_name = TIER_1_MODEL_NAME if model_tier == "tier_1" else TIER_2_MODEL_NAME
        
        # This flag is crucial for structured output to work correctly with Gemini
        self.model = ChatGoogleGenerativeAI(
            model=model_name, 
            temperature=0.0,
        )

        self.model_name = self.model.model
        self.logger.info(f"Initialized {self.agent_name} with model {self.model_name}")
    
    async def __call__(self, state: AgentState) -> AgentState:
        """
        Main entry point for agent execution with logging and error handling.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        start_time = time.time()
        execution_successful = True
        error_message = None
        output_data = None
        
        try:
            self.logger.info(f"Starting execution of {self.agent_name}")
            
            # Pre-execution validation
            self._validate_input_state(state)
            
            # Execute the agent's core logic
            output_data = await self.execute(state)
            
            # Update the state with results
            updated_state = self._update_state(state, output_data)
            
            self.logger.info(f"Successfully completed execution of {self.agent_name}")
            
        except Exception as e:
            execution_successful = False
            error_message = str(e)
            self.logger.error(f"Error in {self.agent_name}: {e}", exc_info=True)
            
            # Handle the error and update state
            updated_state = self._handle_error(state, e)
            output_data = {"error": error_message}
        
        finally:
            # Log execution metrics
            execution_time_ms = (time.time() - start_time) * 1000
            
            updated_state = log_agent_execution(
                state=updated_state if 'updated_state' in locals() else state,
                agent_name=self.agent_name,
                input_data=self._extract_input_summary(state),
                output_data=output_data,
                execution_time_ms=execution_time_ms,
                success=execution_successful,
                error_message=error_message
            )
            
            # Update timing information
            if execution_successful:
                updated_state = updated_state.copy()
                if updated_state.get("performance_metrics") is not None:
                    updated_state["performance_metrics"][f"{self.agent_name}_execution_time_ms"] = execution_time_ms
        
        return updated_state
    
    @abstractmethod
    async def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute the agent's core logic.
        
        This method must be implemented by each concrete agent.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dictionary containing the agent's output data
        """
        pass
    
    def _validate_input_state(self, state: AgentState) -> None:
        """
        Validates that the input state contains required fields.
        
        Args:
            state: Input state to validate
            
        Raises:
            ValueError: If required state fields are missing
        """
        required_fields = ["user_query", "current_step", "workflow_status"]
        
        for field in required_fields:
            if field not in state:
                raise ValueError(f"Required state field '{field}' is missing")
        
        # Agent-specific validation can be overridden
        self._validate_agent_specific_state(state)
    
    def _validate_agent_specific_state(self, state: AgentState) -> None:
        """
        Override this method for agent-specific state validation.
        
        Args:
            state: State to validate
        """
        pass
    
    def _update_state(self, state: AgentState, output_data: Dict[str, Any]) -> AgentState:
        """
        Updates the workflow state with agent output.
        
        Args:
            state: Current state
            output_data: Agent output data
            
        Returns:
            Updated state
        """
        updated_state = state.copy()
        
        # Update with output data
        for key, value in output_data.items():
            updated_state[key] = value
        
        # Agent-specific state updates
        updated_state = self._apply_agent_specific_updates(updated_state, output_data)
        
        return updated_state
    
    def _apply_agent_specific_updates(self, state: AgentState, output_data: Dict[str, Any]) -> AgentState:
        """
        Override this method for agent-specific state updates.
        
        Args:
            state: Current state
            output_data: Agent output data
            
        Returns:
            Updated state
        """
        return state
    
    def _handle_error(self, state: AgentState, error: Exception) -> AgentState:
        """
        Handles errors during agent execution.
        
        Args:
            state: Current state
            error: The exception that occurred
            
        Returns:
            Updated state with error information
        """
        updated_state = state.copy()
        
        # Set error state
        updated_state["error_state"] = {
            "agent": self.agent_name,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.now().isoformat()
        }
        
        # Update workflow status
        updated_state["workflow_status"] = "failed"
        updated_state["current_step"] = "error"
        
        # Track recovery attempts
        if updated_state.get("error_recovery_attempts") is None:
            updated_state["error_recovery_attempts"] = []
        
        updated_state["error_recovery_attempts"].append({
            "agent": self.agent_name,
            "error": str(error),
            "timestamp": datetime.now().isoformat()
        })
        
        return updated_state
    
    def _extract_input_summary(self, state: AgentState) -> Dict[str, Any]:
        """
        Extracts a summary of relevant input data for logging.
        
        Args:
            state: Current state
            
        Returns:
            Summary of input data
        """
        return {
            "user_query": state.get("user_query", "")[:100] + "..." if len(state.get("user_query", "")) > 100 else state.get("user_query", ""),
            "current_step": state.get("current_step"),
            "workflow_status": state.get("workflow_status"),
            "retry_count": state.get("retry_count", 0)
        }
    
    async def generate_content_async(self, prompt: str, **kwargs) -> str:
        """
        Generates content using the agent's model with async support and caching.
        
        Args:
            prompt: The prompt to send to the model
            **kwargs: Additional generation parameters
            
        Returns:
            Generated content text
        """
        if not redis_client:
            # Fallback to direct call if Redis is not available
            self.logger.warning("Redis not available. Calling model directly without caching.")
            response = await self.model.ainvoke(prompt, **kwargs)
            return response.content.strip()

        try:
            # 1. Create a unique, consistent key for the prompt
            prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()
            cache_key = f"prompt_cache:{prompt_hash}"

            # 2. Check the cache first
            cached_response = redis_client.get(cache_key)
            if cached_response:
                self.logger.info("--- CACHE HIT ---")
                return cached_response

            # 3. If not in cache (cache miss), call the model
            self.logger.info("--- CACHE MISS ---")
            response = await self.model.ainvoke(prompt, **kwargs)
            response_text = response.content.strip()

            # 4. Store the new response in the cache with no expiration
            redis_client.set(cache_key, response_text)
            
            return response_text

        except Exception as e:
            self.logger.error(f"Error during content generation or caching: {e}")
            # Fallback to direct call on error
            response = await self.model.ainvoke(prompt, **kwargs)
            return response.content.strip()
    
    def sanitize_for_logging(self, data: Any, max_length: int = 150) -> str:
        """
        Sanitizes data for safe logging.
        
        Args:
            data: Data to sanitize
            max_length: Maximum length for string data
            
        Returns:
            Sanitized string representation
        """
        if data is None:
            return "None"
        
        if isinstance(data, str):
            return data[:max_length] + "..." if len(data) > max_length else data
        
        if isinstance(data, (dict, list)):
            return f"{type(data).__name__} with {len(data)} items"
        
        return str(data)[:max_length] 