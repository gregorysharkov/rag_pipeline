import logging
import re
from typing import Any, List, Dict, Optional

from openai import OpenAI

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class ImprovedScriptWritingAgent(BaseAgent):
    """Agent responsible for writing the script with improved section handling."""

    def __init__(self, client: OpenAI = None):
        super().__init__(
            name="ImprovedScriptWritingAgent",
            description="Writes scripts with enhanced section-specific capabilities.",
            model="o1-2024-12-17",  # Using a more advanced model for better quality
            client=client,
        )

    def run(
        self,
        topic: str,
        plan: dict[str, Any],
        references: list[dict[str, str]],
        section_only: bool = False,
        additional_context: Optional[str] = None,
    ) -> str:
        """
        Write a script based on the topic, plan, and references.

        Args:
            topic: The main topic of the video
            plan: The script plan from the PlanningAgent
            references: List of reference materials from web search
            section_only: If True, generate content for just the section without headers
            additional_context: Optional additional context or requirements

        Returns:
            The script as a string
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

        # Build context section
        context_section = ""
        if additional_context:
            context_section = f"""
            Additional Context:
            {additional_context}
            """

        # Determine if we're generating for a single section or full script
        is_single_section = len(plan.get("sections", [])) == 1

        # Adjust the prompt based on whether we're generating a full script or section content
        if is_single_section and section_only:
            # For section-only content, we need a different approach
            section = plan["sections"][0]

            prompt = f"""
            You are a professional script writer for educational and engaging YouTube videos. Your task is to write content for a specific section of a video about: {topic}

            {context_section}

            Video Details:
            Title: {plan.get("title", "Untitled")}
            Target Audience: {plan.get("target_audience", "General audience")}
            Estimated Duration: {plan.get("duration", "5-10")} minutes

            You are writing ONLY for this section:
            Section: {section["name"]}
            Key Message: {section.get("key_message", "")}
            Points: {", ".join(section["points"])}

            References to incorporate:
            {references_text}

            IMPORTANT INSTRUCTIONS:
            1. Write ONLY the content for this specific section - do NOT include section headers, introductions, or conclusions
            2. Do NOT include "Section X:" or any section numbering in your response
            3. Focus on delivering the key message of this section through the content
            4. Cover all the key points in an organized way
            5. Use a conversational, but professional tone
            6. The content should feel like someone is speaking directly to the camera
            7. Be concise but thorough - aim for content that would take 1-3 minutes to deliver verbally
            8. Do NOT include transitions to other sections
            
            Write ONLY the content for this section, without any section headers or formatting.
            """
        else:
            # For full script generation
            prompt = f"""
            You are a professional script writer for educational and engaging YouTube videos. Your task is to write a complete script for a video about: {topic}

            {context_section}

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
            5. Includes smooth transitions between sections
            6. Ends with a strong conclusion and call to action

            The script should feel like someone is speaking directly to the camera. Include directions for emphasis where appropriate.
            Be sure to convey the key message for each section throughout the content.
            """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional YouTube script writer specializing in educational and engaging content. Write in a conversational tone that connects with viewers.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

        content = response.choices[0].message.content

        # If we're generating section-only content, clean up any section headers
        if is_single_section and section_only:
            content = self._clean_section_headers(content, plan["sections"][0]["name"])

        return content

    def _clean_section_headers(self, content: str, section_name: str) -> str:
        """
        Remove any section headers from the generated content.

        Args:
            content: The generated content
            section_name: The name of the section

        Returns:
            Cleaned content without section headers
        """
        # Remove any lines that look like section headers
        lines = content.split("\n")
        cleaned_lines = []

        for line in lines:
            # Skip lines that look like section headers
            if re.match(
                r"^(?:Section|SECTION|\d+\.)\s*[:|-]?\s*" + re.escape(section_name),
                line,
                re.IGNORECASE,
            ):
                continue
            # Skip generic section headers
            if re.match(r"^(?:Section|SECTION)\s*\d+\s*[:|-]", line, re.IGNORECASE):
                continue
            cleaned_lines.append(line)

        return "\n".join(cleaned_lines)

    def extract_section_content(self, full_script: str, section_name: str) -> str:
        """
        Extract the content specific to a section from a full script.

        Args:
            full_script: The full script text
            section_name: The name of the section to extract

        Returns:
            The extracted section content
        """
        # Try to find the section by name
        pattern = rf"(?i)(?:(?:section|part)\s*[:|-])?\s*{re.escape(section_name)}.*?(?:\n+)(.*?)(?:\n+(?:section|part|conclusion|outro|summary)|\Z)"
        match = re.search(pattern, full_script, re.DOTALL | re.IGNORECASE)

        if match:
            return match.group(1).strip()

        # Fallback to a simple approach
        lines = full_script.strip().split("\n")
        if len(lines) > 3:
            return "\n".join(lines[3:])

        return full_script
