import os
import logging
from dotenv import load_dotenv
from openai import OpenAI

from agents.memory_agent import MemoryAgent
from agents.web_search_agent import WebSearchAgent
from agents.processor_agent import ProcessorAgent
from agents.doc_gen_agent import DocGenAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def create_agents(debug_mode=False):
    """Create agent instances.

    Args:
        debug_mode: Whether to enable debug mode for agents that support it

    Returns:
        Dictionary of agent instances
    """
    # Initialize OpenAI client
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    logger.info("Creating agent instances with client")
    memory_agent = MemoryAgent(client)
    if debug_mode:
        logger.info("Debug mode is enabled - using debug-enabled web search agent")
    web_search_agent = WebSearchAgent(client, debug_mode=debug_mode)
    processor_agent = ProcessorAgent(client)
    doc_gen_agent = DocGenAgent(client)

    return {
        "memory": memory_agent,
        "web_search": web_search_agent,
        "processor": processor_agent,
        "doc_gen": doc_gen_agent,
    }


def main(debug_mode=False):
    """Main function to run the application.

    Args:
        debug_mode: Whether to enable debug mode for agents that support it
    """
    logger.info("Initializing RAG pipeline application")
    logger.info(f"Debug mode: {debug_mode}")

    # Create agents
    agents = create_agents(debug_mode=debug_mode)

    # Here you would add your main application logic
    logger.info("Application initialized successfully")

    return agents


if __name__ == "__main__":
    # You can pass debug_mode=True here for testing
    main(debug_mode=True)
