"""
Implements the Finish Tool for the ReAct Agent.
"""
from react_agent.base_tool import BaseTool

class FinishTool(BaseTool):
    """
    A special tool to signal that the agent has completed its work and is
    ready to provide the final answer to the user.
    """

    @property
    def name(self) -> str:
        return "finish"

    @property
    def description(self) -> str:
        return (
            "Call this tool ONLY when you have gathered all the necessary information "
            "and are ready to provide a final, comprehensive answer to the user's query. "
            "Input: {'answer': 'The final, detailed answer for the user.'}"
        )

    def __call__(self, answer: str) -> dict:
        """
        This tool does not perform any action other than returning the answer.
        The dispatcher will intercept the 'finish' tool name and halt the loop.
        
        Args:
            answer: The final answer formulated by the agent.

        Returns:
            A dictionary containing the final answer.
        """
        return {"answer": answer} 