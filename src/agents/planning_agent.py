import json
import logging
from typing import Any

from openai import OpenAI

from src.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class PlanningAgent(BaseAgent):
    """Agent responsible for planning the script structure."""

    def __init__(self, client: OpenAI = None):
        super().__init__(
            name="PlanningAgent",
            description="Plans the structure and outline of the video script.",
            client=client,
        )

    def run(self, topic: str, references: list[dict[str, str]]) -> dict[str, Any]:
        """
        Generate a plan for the video script based on the topic and references.

        Args:
            topic: The main topic of the video
            references: List of reference materials from web search

        Returns:
            Dictionary containing the script plan
        """
        # Format references for the prompt
        references_text = "\n\n".join(
            [
                f"Reference {i + 1}:\nTitle: {ref['title']}\nURL: {ref['url']}\nSummary: {ref['summary']}"
                for i, ref in enumerate(references)
            ]
        )

        prompt = f"""
        You are a video script planning agent. Your task is to create a detailed plan for a YouTube video about: {topic}

        Here are the references to incorporate:
        {references_text}

        Create a comprehensive plan that includes:
        1. Video title
        2. Target audience
        3. Estimated duration (in minutes)
        4. Key sections with bullet points for each section
        5. Key takeaways

        Format your response as a JSON object with keys: "title", "target_audience", "duration", "sections" (array of objects with "name" and "points"), and "key_takeaways" (array)
        """

        response = self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a helpful video planning assistant."},
                {"role": "user", "content": prompt},
            ],
        )

        # Extract and parse the JSON response
        try:
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Error parsing planning results: {e}")
            return {}
