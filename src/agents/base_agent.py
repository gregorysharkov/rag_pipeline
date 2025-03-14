from typing import Any

from openai import OpenAI


class BaseAgent:
    """Base Agent class that all specialized agents will inherit from."""

    def __init__(self, name: str, description: str, model: str = "gpt-4o", client: OpenAI = None):
        self.name = name
        self.description = description
        self.model = model
        self.client = client

    def run(self, input_data: Any) -> Any:
        """Run the agent's task. To be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement this method")
