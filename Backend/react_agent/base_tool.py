"""
Defines the abstract base class for all tools in the agent's toolkit.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseTool(ABC):
    """
    An abstract base class for a tool that the ReAct agent can use.
    It defines a standard interface for tool execution and description.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """The unique name of the tool."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """A detailed description of what the tool does, its inputs, and its outputs."""
        pass

    @abstractmethod
    def __call__(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Executes the tool with the given keyword arguments.

        Args:
            **kwargs: The arguments required by the tool, as specified in its
                      description.

        Returns:
            A JSON-serializable dictionary containing the result of the tool's execution.
        """
        pass 