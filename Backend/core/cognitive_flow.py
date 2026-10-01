"""
Cognitive Flow Logging.

This module provides the data structures and logger for capturing
and streaming the "Cognitive Flow" of the agent's thinking process.
"""

from typing import Optional, Dict, Any, Literal, Coroutine, AsyncGenerator, List
import asyncio
import contextvars
from pydantic import BaseModel

# The queue for the request currently being processed. Each call to
# get_response_stream sets its own queue here, so concurrent requests never read
# each other's events (asyncio tasks created during the request inherit it).
request_queue: contextvars.ContextVar[Optional[asyncio.Queue]] = contextvars.ContextVar("request_queue", default=None)

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

    def _queue(self) -> asyncio.Queue:
        """The current request's queue, falling back to the shared one."""
        return request_queue.get() or self.queue

    async def emit(self, event: Dict[str, Any]):
        """Puts a structured event (e.g. {"trace": {...}}) on the current request's stream."""
        await self._queue().put(event)

    async def log_step(self, agent_name: str, status: Literal["WORKING", "DONE", "ERROR"], message: str, state: Optional[AgentState] = None):
        """
        Logs a single step in the cognitive flow and optionally updates the AgentState.
        """
        # Always put the string message on the queue for streaming
        await self._queue().put({"cognitive_message": message})

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