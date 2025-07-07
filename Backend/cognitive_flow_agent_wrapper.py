"""
Cognitive Flow Agent Wrapper.

This module provides a wrapper class that adds Cognitive Flow logging
to any agent that it wraps.
"""

from typing import Optional, Dict, Any
from agents.base_agent import BaseLangGraphAgent
from cognitive_flow import CognitiveFlowLogger
from state import AgentState

class CognitiveFlowAgentWrapper:
    """
    Wraps a BaseLangGraphAgent to provide Cognitive Flow logging.
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
        Executes the agent and logs the cognitive flow.
        """
        if self.cognitive_flow_logger:
            await self.cognitive_flow_logger.log_step(
                self.agent_name, "WORKING", f"Starting {self.agent_name}..."
            )
        
        try:
            result = await self.agent(state)
            
            if self.cognitive_flow_logger:
                await self.cognitive_flow_logger.log_step(
                    self.agent_name, "DONE", f"{self.agent_name} complete."
                )
            
            return result
            
        except Exception as e:
            if self.cognitive_flow_logger:
                await self.cognitive_flow_logger.log_step(
                    self.agent_name, "ERROR", f"Error in {self.agent_name}: {e}"
                )
            raise e 