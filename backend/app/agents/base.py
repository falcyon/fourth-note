"""Base agent class and result types for the agentic pipeline."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class AgentResult:
    """Result from an agent execution."""

    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def ok(cls, data: Any, **metadata) -> "AgentResult":
        """Create a successful result."""
        return cls(success=True, data=data, metadata=metadata)

    @classmethod
    def fail(cls, error: str, **metadata) -> "AgentResult":
        """Create a failed result."""
        return cls(success=False, error=error, metadata=metadata)


class BaseAgent(ABC):
    """Base class for all agents in the pipeline.

    Agents are stateless processors that take input data and return a result.
    Each agent focuses on a single task (triage, extraction, LinkedIn lookup, etc.)
    """

    @abstractmethod
    async def run(self, input_data: Any) -> AgentResult:
        """Execute the agent's task.

        Args:
            input_data: The input data for this agent (varies by agent type)

        Returns:
            AgentResult with success/failure status and data/error
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Agent identifier for logging."""
        pass

    def log(self, message: str) -> None:
        """Log a message with agent name prefix."""
        print(f"[{self.name}] {message}")
