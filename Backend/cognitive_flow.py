"""
Cognitive Flow Logging.

This module provides the data structures and logger for capturing
and streaming the "Cognitive Flow" of the agent's thinking process.
"""

from typing import Optional, Dict, Any, Literal, Coroutine, AsyncGenerator, List
import asyncio
from pydantic import BaseModel

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

    async def log_step(self, agent_name: str, status: Literal["WORKING", "DONE", "ERROR"], message: str):
        """
        Logs a single step in the cognitive flow.
        """
        event = CognitiveFlowEvent(
            agent_name=agent_name,
            status=status,
            message=message
        )
        await self.queue.put(event.model_dump_json()) 