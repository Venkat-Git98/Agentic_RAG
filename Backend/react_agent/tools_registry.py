"""
Initializes and registers all available tools for the ReAct agent.
"""
from typing import Dict
from react_agent.base_tool import BaseTool
from tools.planning_tool import PlanningTool
from tools.parallel_research_tool import ParallelResearchTool
from tools.synthesis_tool import SynthesisTool
from tools.finish_tool import FinishTool

def get_tools() -> Dict[str, BaseTool]:
    """
    Instantiates and returns a dictionary of all available tools.
    The keys are the tool names, making them easy to look up.
    """
    tools = [
        PlanningTool(),
        ParallelResearchTool(),
        SynthesisTool(),
        FinishTool()
    ]
    return {tool.name: tool for tool in tools}

def get_tools_description(tools: Dict[str, BaseTool]) -> str:
    """
    Generates a formatted string describing all available tools,
    to be injected into the master agent's prompt.
    """
    return "\n".join(
        f"- `{tool.name}`: {tool.description}" for tool in tools.values()
    )

# --- Pre-initialized instances for the application ---
TOOL_REGISTRY = get_tools()
TOOLS_DESCRIPTION = get_tools_description(TOOL_REGISTRY) 