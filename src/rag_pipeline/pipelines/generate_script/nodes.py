"""
This module contains nodes for the generate_script pipeline.
"""

import logging
import os

import openai
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variables
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    logger.error("OPENAI_API_KEY not found in environment variables")
    raise ValueError("OPENAI_API_KEY not found in environment variables")

# Initialize the OpenAI client
client = openai.OpenAI(api_key=api_key)


def generate_youtube_short_script(topic: str) -> str:
    """
    Generate a script for a YouTube short based on the given topic.

    Args:
        topic: The topic or theme for the YouTube short

    Returns:
        str: The generated script
    """
    logger.info(f"Generating script for topic: {topic}")
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # You can change this to a different model if needed
            messages=[
                {
                    "role": "system",
                    "content": "You are a creative script writer for engaging YouTube shorts.",
                },
                {
                    "role": "user",
                    "content": f"Write a script for a 60-second YouTube short about {topic}. "
                    f"The script should be attention-grabbing, informative, and end with a hook. "
                    f"Format it with clear sections for INTRO, MAIN CONTENT, and OUTRO."
                    f"start with a plan: key messages, hooks and structure of the script",
                },
            ],
            max_tokens=500,
            temperature=0.7,
        )
        logger.debug("Script generated successfully")
        return response.choices[0].message.content
    except Exception as e:
        error_msg = f"Error generating script: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)


def save_script(script: str, save_script: bool = True) -> str:
    """
    Save the generated script to a file if save_script is True.

    Args:
        script: The generated script
        save_script: Whether to save the script to a file

    Returns:
        str: The path to the saved script file or a message indicating the script was not saved
    """
    if not save_script:
        logger.info("Script not saved as per configuration")
        return "Script not saved"

    try:
        # Create scripts directory if it doesn't exist
        os.makedirs("data/08_reporting/scripts", exist_ok=True)

        # Generate a filename based on the first line of the script
        first_line = script.split("\n")[0][:30].strip()
        safe_name = "".join(c if c.isalnum() else "_" for c in first_line)
        filename = f"data/08_reporting/scripts/{safe_name}.txt"

        # Save the script to the file
        with open(filename, "w") as f:
            f.write(script)

        logger.info(f"Script saved to {filename}")
        return filename
    except Exception as e:
        error_msg = f"Error saving script to file: {str(e)}"
        logger.error(error_msg)
        return f"Error: {error_msg}"
