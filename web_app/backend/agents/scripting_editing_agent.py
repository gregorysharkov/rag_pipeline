import logging
from openai import OpenAI
import re
import os
from dotenv import load_dotenv


class ScriptEditingAgent:
    """Agent responsible for editing and enhancing scripts based on user preferences."""

    def __init__(self, client=None):
        """Initialize the ScriptEditingAgent.

        Args:
            client: An instance of the OpenAI client (optional).
        """
        self.logger = logging.getLogger(__name__)
        
        # Load environment variables
        load_dotenv()
        
        # Initialize client if not provided
        if client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key not found in environment variables")
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = client

        # Define the available editing options and their descriptions
        self.edit_options = {
            "conversational": "Make the script more conversational and natural-sounding for speech",
            "rhetorical": "Add rhetorical questions to engage the audience",
            "humor": "Add appropriate humor where it fits naturally",
            "transitions": "Improve transitions between sections to make the flow smoother",
            "flow": "Ensure the script flows naturally when read aloud",
            "analogies": "Add relevant analogies to explain complex concepts",
            "simplify": "Simplify language to make it more accessible to the target audience",
            "scene_descriptions": "Add scene descriptions in [SCENE: description] format",
            "visuals": "Add visual cues and suggestions in [VISUAL: description] format",
            "cuts": "Add camera cuts and transitions in [CUT TO: description] format",
            "b_roll": "Suggest B-roll footage in [B-ROLL: description] format",
            "graphics": "Add on-screen text and graphics suggestions in [GRAPHIC: description] format",
        }

    def edit_script(
        self, original_script: str, edit_options: list, additional_instructions: str = ""
    ) -> str:
        """Edit the script based on the selected options and instructions.

        This is a convenience method that calls run() internally.

        Args:
            original_script: The original script content to edit.
            edit_options: A list of editing options selected by the user.
            additional_instructions: Any additional user instructions.

        Returns:
            str: The edited script content.
        """
        return self.run(original_script, edit_options, additional_instructions)

    def run(
        self, original_script: str, edit_options: list, additional_instructions: str = ""
    ) -> str:
        """Edit the script based on the selected options and instructions.

        Args:
            original_script: The original script content to edit.
            edit_options: A list of editing options selected by the user.
            additional_instructions: Any additional user instructions.

        Returns:
            str: The edited script content.
        """
        self.logger.info(f"Editing script with options: {edit_options}")
        self.logger.info(f"Original script length: {len(original_script)}")

        # Create a prompt for the LLM based on selected options
        prompt = self._create_editing_prompt(original_script, edit_options, additional_instructions)

        try:
            # Call the LLM to edit the script
            self.logger.info("Calling LLM to edit script")
            response = self.client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional script editor who enhances scripts to make them more engaging and effective.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=4000,
            )

            # Extract the edited script from the response
            edited_script = response.choices[0].message.content
            self.logger.info(f"Successfully edited script. New length: {len(edited_script)}")

            # Check if all sections are properly formatted
            if "**[" not in edited_script:
                self.logger.warning("Section headers not found in edited script. Adding them back.")
                # The model might have removed the section headers, try to add them back
                if original_script and "**[" in original_script:
                    section_matches = re.findall(r"\*\*\[(.*?)\]\*\*", original_script)
                    if section_matches:
                        # Split the content by existing patterns or paragraphs
                        paragraphs = edited_script.split("\n\n")
                        section_count = len(section_matches)
                        paragraphs_per_section = max(1, len(paragraphs) // section_count)

                        # Rebuild the script with section headers
                        new_script = ""
                        section_index = 0

                        for i in range(0, len(paragraphs), paragraphs_per_section):
                            if section_index < section_count:
                                new_script += f"**[{section_matches[section_index]}]**\n\n"
                                section_index += 1

                            end_idx = min(i + paragraphs_per_section, len(paragraphs))
                            new_script += "\n".join(paragraphs[i:end_idx]) + "\n\n"

                        edited_script = new_script
                        self.logger.info("Reconstructed script with section headers")

            return edited_script

        except Exception as e:
            self.logger.error(f"Error editing script: {str(e)}")
            raise e

    def _create_editing_prompt(
        self, original_script: str, edit_options: list, additional_instructions: str
    ) -> str:
        """Create a prompt for the editing request based on selected options.

        Args:
            original_script: The original script content.
            edit_options: List of editing options selected by the user.
            additional_instructions: Any additional instructions from the user.

        Returns:
            str: The prompt to send to the LLM.
        """
        # Base prompt
        prompt = f"""You are an expert script editor. Your task is to edit the following script according to provided instructions.
The script is separated in sections using the following pattern `**section_name**`, please edit each section separately.

ORIGINAL SCRIPT:
{original_script}

EDITING REQUIREMENTS:
"""

        # Add selected options to the prompt with their descriptions
        for option in edit_options:
            if option in self.edit_options:
                prompt += f"- {self.edit_options[option]}\n"
            else:
                prompt += f"- {option}\n"

        # Add additional instructions
        if additional_instructions:
            prompt += f"\nADDITIONAL INSTRUCTIONS:\n{additional_instructions}\n"

        # Final instructions
        prompt += """
CRITICAL FORMATTING REQUIREMENTS:
1. You MUST maintain the original section headers in the format **[Section Title]**
2. Each section must begin with its header in the format **[Section Title]**
3. DO NOT remove, change, or reorder the section headers
4. DO NOT add new section headers
5. KEEP the exact same section titles as in the original script

IMPORTANT CONTENT GUIDELINES:
1. Preserve the key messages and essential points from the original script
2. The edited script should be of similar length to the original
3. Format the script clearly with proper paragraphing and spacing
4. Visual elements should be clearly marked with brackets (e.g., [VISUAL: description])

Please provide the complete edited script with all original section headers preserved:"""

        return prompt
