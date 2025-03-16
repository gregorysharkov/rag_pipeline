import logging
from typing import Any

from openai import OpenAI

from src.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class ShortVideoAgent(BaseAgent):
    """Agent responsible for creating a short promotional video script."""

    def __init__(self, client: OpenAI = None):
        super().__init__(
            name="ShortVideoAgent",
            description="Creates a punchy 30-second promotional script for vertical short-form video.",
            client=client,
        )

    def run(self, topic: str, full_script: str, plan: dict[str, Any]) -> str:
        """
        Create a short 30-second promotional script based on the full video script.

        Args:
            topic: The main topic of the video
            full_script: The complete edited script of the main video
            plan: The script plan with key points and takeaways

        Returns:
            A short promotional script for vertical video format
        """
        # Extract key takeaways for the prompt
        key_takeaways = ", ".join(plan.get("key_takeaways", []))

        prompt = f"""
        You are a short-form video script specialist. Your task is to create a punchy, attention-grabbing 
        30-second promotional script for a vertical short video about: {topic}

        This short video will promote a longer horizontal video on the same topic.

        Here are the key takeaways from the main video:
        {key_takeaways}

        The full script of the main video is:
        {full_script[:1000]}... [truncated for brevity]

        Create a 30-second script that:
        1. Hooks the viewer in the first 3 seconds
        2. Teases the most interesting points from the main video
        3. Creates curiosity and a desire to watch the full video
        4. Ends with a clear call to action to watch the full video
        5. Is optimized for vertical viewing (9:16 aspect ratio)
        6. Uses punchy, concise language suitable for short-form content
        7. Is approximately 75-100 words (suitable for 30 seconds of speaking)

        Format the script with clear sections for HOOK, TEASER, and CALL TO ACTION.
        """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a short-form video script specialist."},
                {"role": "user", "content": prompt},
            ],
        )

        return response.choices[0].message.content
