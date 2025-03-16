import json
import logging
from typing import Any, Optional

from openai import OpenAI

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class PlanningAgent(BaseAgent):
    """Agent responsible for planning the script structure."""

    def __init__(self, client: OpenAI = None):
        super().__init__(
            name="PlanningAgent",
            description="Plans the structure and outline of the video script.",
            model="o1-2024-12-17",  # Using the latest model for better planning capabilities
            client=client,
        )

    def run(
        self, topic: str, references: list[dict[str, str]], additional_context: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Generate a plan for the video script based on the topic, references, and additional context.

        Args:
            topic: The main topic of the video
            references: List of reference materials from web search
            additional_context: Optional additional context or requirements from the user

        Returns:
            Dictionary containing the script plan with title, target audience, duration,
            sections (each with name, points, and key_message), and key takeaways
        """
        # Format references for the prompt
        references_text = "\n\n".join(
            [
                f"Reference {i + 1}:\nTitle: {ref['title']}\nURL: {ref['url']}\nSummary: {ref['summary']}"
                for i, ref in enumerate(references)
            ]
        )

        # Build the prompt with optional additional context
        context_section = (
            f"\nUser provided additional context:\n{additional_context}"
            if additional_context
            else ""
        )

        prompt = f"""
        You are a video script planning agent. Your task is to create a detailed plan for a YouTube video about: {
            topic
        }
        {context_section}

        Here are the references to incorporate:
        {references_text}

        Create a comprehensive plan that incorporates the topic, {
            "the user provided additional context, " if additional_context else ""
        }and the references, that includes:
        1. Video title (engaging and SEO-friendly)
        2. Target audience (be specific about who would benefit most from this content)
        3. Estimated duration (in minutes)
        4. Key sections (each with specific points and a clear key message)

        Format your response as a JSON object with these keys:
        - "title": string (the video title)
        - "target_audience": string (detailed description of the target audience)
        - "duration": number (estimated length in minutes)
        - "sections": array of objects, each with:
          - "name": string (section name)
          - "points": array of strings (bullet points to cover)
          - "key_message": string (main takeaway from this section)
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional video content strategist specializing in creating engaging and educational content plans.",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )

            # Extract and parse the JSON response
            plan = json.loads(response.choices[0].message.content)

            # Log successful planning
            logger.info(f"Successfully created video plan for topic: {topic}")
            logger.debug(
                f"Plan sections: {[section['name'] for section in plan.get('sections', [])]}"
            )

            return plan

        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {e}")
            raise ValueError(f"Failed to parse JSON response from model: {e}")
        except Exception as e:
            logger.error(f"Error during planning: {e}")
            raise Exception(f"Error during plan generation: {e}")
