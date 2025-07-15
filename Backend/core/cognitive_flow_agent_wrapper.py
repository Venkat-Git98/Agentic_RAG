"""
Cognitive Flow Agent Wrapper.

This module provides a wrapper class that adds Cognitive Flow logging
to any agent that it wraps, with human-like "thinking" messages.
"""

import random
from typing import Optional, Dict, Any
from agents.base_agent import BaseLangGraphAgent
from .cognitive_flow import CognitiveFlowLogger
from .state import AgentState
from .thinking_messages import THINKING_MESSAGES

class CognitiveFlowAgentWrapper:
    """
    Wraps a BaseLangGraphAgent to provide human-like Cognitive Flow logging.
    """
    def __init__(self, agent: BaseLangGraphAgent, cognitive_flow_logger: Optional[CognitiveFlowLogger] = None):
        """
        Initializes the wrapper.
        
        Args:
            agent: The agent instance to wrap.
            cognitive_flow_logger: The logger for cognitive flow updates.
        """
        self.agent = agent
        self.cognitive_flow_logger = cognitive_flow_logger
        self.agent_name = agent.agent_name

    async def __call__(self, state: AgentState) -> Dict[str, Any]:
        """
        Executes the agent and logs the cognitive flow with human-like messages.
        """
        if self.cognitive_flow_logger:
            # Select a random "thinking" message for the current agent
            thinking_message = random.choice(
                THINKING_MESSAGES.get(self.agent_name, [f"Starting {self.agent_name}..."])
            )
            await self.cognitive_flow_logger.log_step(
                self.agent_name, "WORKING", thinking_message, state
            )
        
        try:
            result = await self.agent(state)
            
            log_message = None
            # Check if the agent's result contains detailed reasoning
            if "reasoning" in result and result["reasoning"]:
                log_message = result["reasoning"]
            
            # If no detailed reasoning, fall back to a generic thinking message
            if not log_message:
                log_message = random.choice(
                    THINKING_MESSAGES.get(self.agent_name, [f"{self.agent_name} finished."])
                )

            if self.cognitive_flow_logger:
                await self.cognitive_flow_logger.log_step(
                    self.agent_name, "DONE", log_message, state
                )
            
            return result
            
        except Exception as e:
            if self.cognitive_flow_logger:
                error_message = random.choice(
                    THINKING_MESSAGES.get("ErrorHandler", [f"Error in {self.agent_name}: {e}"])
                )
                await self.cognitive_flow_logger.log_step(
                    self.agent_name, "ERROR", error_message
                )
            raise e 