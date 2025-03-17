import os
import logging
import sys
from dotenv import load_dotenv
from openai import OpenAI

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("web_search_test.log")],
)

logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import from src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.agents.web_search_agent import WebSearchAgent


def main():
    # Load environment variables
    load_dotenv()

    # Initialize OpenAI client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY not found in environment variables")
        return

    logger.info(f"API key found: {api_key[:5]}...{api_key[-5:]}")
    client = OpenAI(api_key=api_key)

    # Initialize WebSearchAgent
    web_search_agent = WebSearchAgent(client)

    # Test topic
    topic = "The impact of AI on fraud detection"

    # Run the search
    logger.info(f"Running web search for topic: {topic}")
    try:
        results = web_search_agent.run(topic)

        # Print results
        if results:
            logger.info(f"Found {len(results)} search results:")
            for i, result in enumerate(results, 1):
                logger.info(f"Result {i}:")
                logger.info(f"Title: {result.get('title')}")
                logger.info(f"URL: {result.get('url')}")
                logger.info(f"Summary: {result.get('summary')[:100]}...")
        else:
            logger.warning("No search results found")

    except Exception as e:
        logger.error(f"Error running web search: {str(e)}")


if __name__ == "__main__":
    main()
