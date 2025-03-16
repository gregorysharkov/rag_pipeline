import logging

from openai import OpenAI

from src.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class ScriptEditingAgent(BaseAgent):
    """Agent responsible for editing and improving the script."""

    def __init__(self, client: OpenAI = None):
        super().__init__(
            name="ScriptEditingAgent",
            description="Edits and improves the script to make it more engaging and human-like.",
            client=client,
        )

    def run(self, script: str, topic: str) -> str:
        """
        Edit and improve the script to make it more engaging and human-like.

        Args:
            script: The initial script to edit
            topic: The main topic of the video

        Returns:
            The edited script as a string
        """
        prompt = f"""
        You are a video script editing agent. Your task is to edit and improve this script about {topic} to make it more engaging, conversational, and human-like.

        Original Script:
        {script}

        Please:
        1. Add more conversational elements and natural speech patterns
        2. Include rhetorical questions to engage the audience
        3. Add humor where appropriate
        4. Improve transitions between sections
        5. Ensure the script flows naturally when read aloud
        6. Keep the same information and structure, just make it more engaging
        7. Add analogies where appropriate
        8. Simplify the language to make it more accessible

        Return the complete edited script.
        """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful script editing assistant."},
                {"role": "user", "content": prompt},
            ],
        )

        return response.choices[0].message.content
