"""Base class for agent tools."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ToolResult:
    """Result from executing a tool."""
    success: bool
    message: str
    data: dict = field(default_factory=dict)


class BaseTool(ABC):
    """Abstract base class for all agent tools."""

    name: str = "base_tool"
    description: str = "Base tool"

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with the given parameters."""
        ...

    def to_dict(self) -> dict:
        """Convert tool to a dictionary for the API."""
        return {
            "name": self.name,
            "description": self.description,
        }
