from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from langchain_core.tools import BaseTool
from app.graph.state import AnalysisState

class BaseAgent(ABC):
    """
    Base class for all LangGraph & LangChain Agents in the Graph Analytics workflow.
    Every agent possesses a defined name, persona/role description, optional tools,
    and a structured invoke method operating over AnalysisState.
    """
    name: str = "BaseAgent"
    role: str = "Assistant"
    description: str = "General agent"
    tools: List[BaseTool] = []

    def __init__(
        self,
        name: Optional[str] = None,
        role: Optional[str] = None,
        description: Optional[str] = None,
        tools: Optional[List[BaseTool]] = None
    ):
        if name:
            self.name = name
        if role:
            self.role = role
        if description:
            self.description = description
        if tools is not None:
            self.tools = tools

    @abstractmethod
    def invoke(self, state: AnalysisState) -> Dict[str, Any]:
        """
        Executes the agent's reasoning loop or tool interaction and returns state delta.
        """
        pass

    def __call__(self, state: AnalysisState) -> Dict[str, Any]:
        """
        Allows the agent instance to be directly plugged into LangGraph workflow.add_node().
        """
        return self.invoke(state)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r} role={self.role!r}>"
