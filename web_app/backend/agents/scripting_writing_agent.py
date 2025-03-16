import logging
from typing import Any

from openai import OpenAI

from src.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class ScriptWritingAgent(BaseAgent):
    """Agent responsible for writing the initial script."""

    def __init__(self, client: OpenAI = None):
        super().__init__(
            name="ScriptWritingAgent",
            description="Writes the initial draft of the video script.",
            client=client,
        )

    def run(self, topic: str, plan: dict[str, Any], references: list[dict[str, str]]) -> str:
        """
        Write a script based on the topic, plan, and references.

        Args:
            topic: The main topic of the video
            plan: The script plan from the PlanningAgent
            references: List of reference materials from web search

        Returns:
            The initial script as a string
        """
        # Format the plan for the prompt
        sections_text = "\n\n".join(
            [
                f"Section: {section['name']}\nPoints: {', '.join(section['points'])}"
                for section in plan.get("sections", [])
            ]
        )

        references_text = "\n\n".join(
            [
                f"Reference {i + 1}:\nTitle: {ref['title']}\nURL: {ref['url']}\nSummary: {ref['summary']}"
                for i, ref in enumerate(references)
            ]
        )

        prompt = f"""
        You are a video script writing agent. Your task is to write a complete script for a YouTube video about: {topic}

        Use this plan:
        Title: {plan.get("title", "Untitled")}
        Target Audience: {plan.get("target_audience", "General audience")}
        Estimated Duration: {plan.get("duration", "5-10")} minutes

        Sections:
        {sections_text}

        Key Takeaways:
        {", ".join(plan.get("key_takeaways", []))}

        References to incorporate:
        {references_text}

        Write a complete script that includes:
        1. Introduction with hook
        2. All sections from the plan
        3. Conclusion with call to action

        Format the script as a video narration with clear section headers.
        """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful script writing assistant."},
                {"role": "user", "content": prompt},
            ],
        )

        return response.choices[0].message.content
