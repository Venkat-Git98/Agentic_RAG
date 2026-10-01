"""
Cognitive Flow Agent Wrapper.

This module provides a wrapper class that adds Cognitive Flow logging
to any agent that it wraps, with human-like "thinking" messages.
"""

import asyncio
import random
import time
from typing import Optional, Dict, Any
from agents.base_agent import BaseLangGraphAgent
from .cognitive_flow import CognitiveFlowLogger
from .state import AgentState
from .thinking_messages import THINKING_MESSAGES

def _plan_item_text(item: Any) -> str:
    if isinstance(item, dict):
        return str(item.get("sub_query") or item.get("query") or "")
    return str(item)


def build_trace_detail(agent_name: str, result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Summarises what an agent actually did, from the state it returned, for the
    frontend's run trace. Only reports facts present in the state.
    """
    if agent_name == "TriageAgent":
        return {"route": result.get("triage_classification"), "reason": result.get("triage_reasoning")}
    if agent_name == "PlanningAgent":
        plan = result.get("research_plan") or []
        return {"sub_questions": [t for t in (_plan_item_text(i) for i in plan) if t],
                "calculation": bool(result.get("math_calculation_needed"))}
    if agent_name == "HydeAgent":
        return {"documents": len(result.get("research_plan") or [])}
    if agent_name == "ResearchOrchestrator":
        answers = result.get("sub_query_answers") or []
        return {"searches": [{
            "question": a.get("sub_query", ""),
            "method": a.get("retrieval_method") or a.get("retrieval_strategy"),
            "relevant": bool(a.get("is_relevant")),
            "context_chars": len(a.get("answer") or ""),
        } for a in answers]}
    if agent_name == "ContextualAnsweringAgent":
        return {"answered_from_conversation": bool(result.get("final_answer"))}
    if agent_name in ("SynthesisAgent", "EnhancedSynthesisAgent"):
        return {"answer_chars": len(result.get("final_answer") or ""),
                "calculation": bool(result.get("math_calculation_needed"))}
    return {}


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
        
        started = time.time()
        if self.cognitive_flow_logger:
            await self.cognitive_flow_logger.emit({"trace": {"agent": self.agent_name, "status": "start"}})
            # Several agents make blocking model calls. Yield briefly so the "start"
            # event reaches the client before the event loop is held up.
            await asyncio.sleep(0.05)

        try:
            result = await self.agent(state)

            if self.cognitive_flow_logger:
                await self.cognitive_flow_logger.emit({"trace": {
                    "agent": self.agent_name,
                    "status": "done",
                    "ms": int((time.time() - started) * 1000),
                    "detail": build_trace_detail(self.agent_name, result or {}),
                }})
            
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
                await self.cognitive_flow_logger.emit({"trace": {
                    "agent": self.agent_name, "status": "error",
                    "ms": int((time.time() - started) * 1000), "detail": {"error": str(e)[:300]},
                }})
            raise e 