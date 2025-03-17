import os
import logging
import json
import sys
import traceback
from dotenv import load_dotenv
from openai import OpenAI
import datetime

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("web_search_full_debug.log")],
)

logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
logger.info(f"Python path: {sys.path}")


def direct_api_test():
    """Test the OpenAI API directly without the agent class"""
    logger.info("=== Testing direct API call ===")

    # Initialize OpenAI client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY not found in environment variables")
        return False

    logger.info(f"API key found: {api_key[:5]}...{api_key[-5:]}")
    client = OpenAI(api_key=api_key)

    topic = "The impact of AI on fraud detection"
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")

    prompt = f"""
    You are a web search specialist with access to the latest information up to {current_date}.
    Your task is to search the web for the most relevant and up-to-date information on the given topic.
    Return exactly 5 high-quality search results that would be most helpful for someone creating content on this topic.

    For each result, provide:
    1. A title - use the actual title from the webpage
    2. The URL - use the actual URL of the webpage, never create fictional URLs
    3. A brief summary of the content (100-150 words) based on the actual content of the page

    IMPORTANT:
    - Only return results from real websites that you've actually found through search
    - Do not generate fictional or example results
    - Do not use example.com or any placeholder domains
    - Ensure all URLs are from legitimate websites
    - If you cannot find enough results, return fewer than 5 rather than making up results
    
    Format each result as follows:
    
    ## Result 1
    Title: [Title of the webpage]
    URL: [URL of the webpage]
    Summary: [Brief summary of the content]
    
    ## Result 2
    ...and so on
    """

    user_message = f"Search the web for information about: {topic}"

    try:
        logger.info(f"Sending request to API with model: gpt-4o-search-preview")
        logger.info(f"User message: {user_message}")

        response = client.chat.completions.create(
            model="gpt-4o-search-preview",
            messages=[
                {
                    "role": "system",
                    "content": prompt,
                },
                {
                    "role": "user",
                    "content": user_message,
                },
            ],
        )

        logger.info("API call successful")
        logger.info(f"Response model: {response.model}")
        logger.info(f"Response ID: {response.id}")

        content = response.choices[0].message.content
        logger.info(f"Response content first 200 chars: {content[:200]}...")

        return True
    except Exception as e:
        logger.error(f"Error making API call: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False


def agent_test():
    """Test using the WebSearchAgent"""
    logger.info("=== Testing WebSearchAgent ===")

    try:
        # Try to import the WebSearchAgent
        from src.agents.web_search_agent import WebSearchAgent

        logger.info("Successfully imported WebSearchAgent")
    except Exception as e:
        logger.error(f"Failed to import WebSearchAgent: {e}")
        logger.error(traceback.format_exc())
        return False

    # Initialize OpenAI client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY not found in environment variables")
        return False

    client = OpenAI(api_key=api_key)

    try:
        # Initialize WebSearchAgent
        web_search_agent = WebSearchAgent(client)
        logger.info("WebSearchAgent initialized successfully")

        # Test topic
        topic = "The impact of AI on fraud detection"

        # Run the search
        logger.info(f"Running web search for topic: {topic}")
        results = web_search_agent.run(topic)

        # Print results
        if results:
            logger.info(f"Found {len(results)} search results:")
            for i, result in enumerate(results, 1):
                logger.info(f"Result {i}:")
                logger.info(f"Title: {result.get('title')}")
                logger.info(f"URL: {result.get('url')}")
                logger.info(f"Summary: {result.get('summary')[:100]}...")
            return True
        else:
            logger.warning("No search results found from WebSearchAgent")
            return False

    except Exception as e:
        logger.error(f"Error in agent_test: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False


def main():
    # Load environment variables
    load_dotenv()

    logger.info("Starting web search debug")

    # Test direct API call
    api_success = direct_api_test()
    logger.info(f"Direct API test {'succeeded' if api_success else 'failed'}")

    # Test WebSearchAgent
    agent_success = agent_test()
    logger.info(f"WebSearchAgent test {'succeeded' if agent_success else 'failed'}")

    if api_success and not agent_success:
        logger.info("The issue appears to be with the WebSearchAgent implementation, not the API")
    elif not api_success and not agent_success:
        logger.info("The issue appears to be with the API or API key permissions")
    elif api_success and agent_success:
        logger.info("Both tests passed - the issue must be elsewhere in the application")


if __name__ == "__main__":
    main()
