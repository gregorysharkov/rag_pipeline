import logging
import os
import sys
from pathlib import Path

# Add the parent directory to the Python path
parent_dir = str(Path(__file__).parent.parent.parent)
sys.path.append(parent_dir)

from dotenv import load_dotenv
from openai import OpenAI

# Import the ScriptEditingAgent
from web_app.backend.agents.scripting_editing_agent import ScriptEditingAgent

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    # Load environment variables
    load_dotenv()

    # Get OpenAI API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("No OPENAI_API_KEY found in environment variables")
        sys.exit(1)

    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)

    # Sample script to edit
    sample_script = """**[Introduction]**

Welcome to our tutorial on Python programming. Python is a versatile language used in many applications.

**[Getting Started]**

To get started with Python, you'll need to install it first. You can download Python from python.org.

**[Basic Syntax]**

Python uses indentation to define code blocks. This makes the code readable and clean.
"""

    # Test with various edit options
    edit_options = ["conversational", "humor"]
    additional_instructions = "Add examples where appropriate"

    # Initialize the ScriptEditingAgent
    try:
        # First try without client parameter
        logger.info("Testing ScriptEditingAgent without client parameter")
        agent = ScriptEditingAgent()
        edited_script = agent.edit_script(sample_script, edit_options, additional_instructions)
        print("\n===== EDITED SCRIPT (No Client) =====")
        print(edited_script)

        # Then try with client parameter
        logger.info("Testing ScriptEditingAgent with client parameter")
        agent_with_client = ScriptEditingAgent(client=client)
        edited_script_with_client = agent_with_client.run(
            sample_script, edit_options, additional_instructions
        )
        print("\n===== EDITED SCRIPT (With Client) =====")
        print(edited_script_with_client)

    except Exception as e:
        logger.error(f"Error testing ScriptEditingAgent: {str(e)}", exc_info=True)
        sys.exit(1)

    logger.info("Script editing test completed successfully")


if __name__ == "__main__":
    main()
