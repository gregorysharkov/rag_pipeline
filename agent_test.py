import json
import logging
import os
import time
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from src.agents.planning_agent import PlanningAgent
from src.agents.scripting_editing_agent import ScriptEditingAgent
from src.agents.scripting_writing_agent import ScriptWritingAgent
from src.agents.short_writing_agent import ShortVideoAgent
from src.agents.web_search_agent import WebSearchAgent

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)


class YouTubeScriptWorkflow:
    """Orchestrates the entire workflow for generating YouTube video scripts."""

    def __init__(self, client: OpenAI):
        self.web_search_agent = WebSearchAgent(client)
        self.planning_agent = PlanningAgent(client)
        self.script_writing_agent = ScriptWritingAgent(client)
        self.script_editing_agent = ScriptEditingAgent(client)
        self.short_video_agent = ShortVideoAgent(client)

    def run(self, topic: str) -> dict[str, Any]:
        """
        Run the complete workflow to generate a YouTube video script.

        Args:
            topic: The topic for the YouTube video

        Returns:
            Dictionary containing all artifacts from the workflow
        """
        logger.info(f"Starting YouTube script generation workflow for topic: {topic}")

        # Step 1: Web Search
        logger.info("1. Performing web search...")
        references = self.web_search_agent.run(topic)
        logger.info(f"Found {len(references)} references")

        # Step 2: Planning
        logger.info("2. Creating script plan...")
        plan = self.planning_agent.run(topic, references)
        logger.info(f"Created plan with {len(plan.get('sections', []))} sections")

        # Step 3: Script Writing
        logger.info("3. Writing initial script...")
        initial_script = self.script_writing_agent.run(topic, plan, references)
        logger.info(f"Initial script written ({len(initial_script.split())} words)")

        # Step 4: Script Editing
        logger.info("4. Editing and improving script...")
        final_script = self.script_editing_agent.run(initial_script, topic)
        logger.info(f"Final script ready ({len(final_script.split())} words)")

        # Step 5: Short Video Script
        logger.info("5. Creating promotional short video script...")
        short_video_script = self.short_video_agent.run(topic, final_script, plan)
        logger.info(f"Short video script ready ({len(short_video_script.split())} words)")

        # Return all artifacts
        return {
            "topic": topic,
            "references": references,
            "plan": plan,
            "initial_script": initial_script,
            "final_script": final_script,
            "short_video_script": short_video_script,
        }


def save_results(results: dict[str, Any], output_dir: str = "output"):
    """Save the workflow results to files."""
    os.makedirs(output_dir, exist_ok=True)

    # Create a timestamp for unique filenames
    timestamp = time.strftime("%Y%m%d_%H%M%S")

    # Save references
    with open(f"{output_dir}/references_{timestamp}.json", "w") as f:
        json.dump(results["references"], f, indent=2)

    # Save plan
    with open(f"{output_dir}/plan_{timestamp}.json", "w") as f:
        json.dump(results["plan"], f, indent=2)

    # Save initial script
    with open(f"{output_dir}/initial_script_{timestamp}.txt", "w") as f:
        f.write(results["initial_script"])

    # Save final script
    with open(f"{output_dir}/final_script_{timestamp}.txt", "w") as f:
        f.write(results["final_script"])

    # Save short video script
    with open(f"{output_dir}/short_video_script_{timestamp}.txt", "w") as f:
        f.write(results["short_video_script"])

    logger.info(f"All results saved to {output_dir}/ directory")


def main():
    """Main function to run the YouTube script generation workflow."""
    # Check for API key
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable not set")
        return

    # Get topic from user
    topic = input("Enter the topic for your YouTube video: ")

    # Run the workflow
    workflow = YouTubeScriptWorkflow(client)
    results = workflow.run(topic)

    # Save results
    save_results(results)

    # Print final scripts
    logger.info("=== FINAL SCRIPT ===")
    print(results["final_script"])

    logger.info("\n=== SHORT VIDEO SCRIPT ===")
    print(results["short_video_script"])


if __name__ == "__main__":
    main()
