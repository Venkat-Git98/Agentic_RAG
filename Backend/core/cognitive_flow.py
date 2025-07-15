"""
Cognitive Flow Logging.

This module provides the data structures and logger for capturing
and streaming the "Cognitive Flow" of the agent's thinking process.
"""

from typing import Optional, Dict, Any, Literal, Coroutine, AsyncGenerator, List
import asyncio
from pydantic import BaseModel

from .state import AgentState # Import AgentState

class CognitiveFlowEvent(BaseModel):
    """
    Represents a single event in the cognitive flow.
    """
    agent_name: str
    status: Literal["WORKING", "DONE", "ERROR"]
    message: str
    
class CognitiveFlowLogger:
    """
    Manages the logging of cognitive flow events.
    """
    def __init__(self, queue: asyncio.Queue):
        """
        Initializes the logger with a queue.
        
        Args:
            queue: The queue to which cognitive flow events will be added.
        """
        self.queue = queue

    async def log_step(self, agent_name: str, status: Literal["WORKING", "DONE", "ERROR"], message: str, state: Optional[AgentState] = None):
        """
        Logs a single step in the cognitive flow and optionally updates the AgentState.
        """
        # Always put the string message on the queue for streaming
        await self.queue.put({"cognitive_message": message})

        if state is not None:
            # For the internal state, we can log the structured event
            event_data = {
                "agent_name": agent_name,
                "status": status,
                "message": message
            }
            # Ensure cognitive_flow_messages is initialized as a list
            if "cognitive_flow_messages" not in state or not isinstance(state["cognitive_flow_messages"], list):
                state["cognitive_flow_messages"] = []
            state["cognitive_flow_messages"].append(event_data) 