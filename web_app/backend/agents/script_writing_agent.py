import logging
from typing import Any

from openai import OpenAI

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class ScriptWritingAgent(BaseAgent):
    """Agent responsible for writing the initial script."""

    def __init__(self, client: OpenAI = None):
        super().__init__(
            name="ScriptWritingAgent",
            description="Writes the initial draft of the video script.",
            model="o3-mini",  # Using a simple reasoning model
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
                f"Section: {section['name']}\nKey Message: {section.get('key_message', '')}\nPoints: {', '.join(section['points'])}"
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
        You are a professional script writer for educational and engaging YouTube videos. Your task is to write a script for a video about: {topic}

        Use this plan:
        Title: {plan.get("title", "Untitled")}
        Target Audience: {plan.get("target_audience", "General audience")}
        Estimated Duration: {plan.get("duration", "5-10")} minutes

        Sections:
        {sections_text}

        References to incorporate:
        {references_text}

        Write a compelling script that:
        1. Has an engaging introduction that hooks the viewer
        2. Clearly communicates the key message of each section
        3. Covers all the key points in an organized way
        4. Uses a conversational, but professional tone
        5. Includes transitions between sections
        6. Ends with a strong conclusion and call to action

        The script should feel like someone is speaking directly to the camera. Include directions for emphasis where appropriate.
        Be sure to convey the key message for each section throughout the content.
        """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": "You are a professional YouTube script writer specializing in educational and engaging content. Write in a conversational tone that connects with viewers.\n\n"
                    + prompt,
                }
            ],
        )

        return response.choices[0].message.content
