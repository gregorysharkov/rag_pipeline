import logging

import requests
from bs4 import BeautifulSoup

from web_app.backend.agents.research_agent.youtube_transcript_generator import (
    YoutubeTranscriptGenerator,
)
from web_app.logging.logger import setup_logging

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)


def fetch_webpage_content(url: str) -> str:
    """Fetch and extract the main content from a webpage."""
    try:
        logger.info(f"Fetching content from URL: {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text content
        text = soup.get_text()

        # Break into lines and remove leading/trailing space
        lines = (line.strip() for line in text.splitlines())

        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))

        # Drop blank lines
        text = " ".join(chunk for chunk in chunks if chunk)

        logger.info(f"Successfully extracted content from {url}")
        return text
    except Exception as e:
        logger.error(f"Error fetching content from {url}: {str(e)}")
        return ""


def fetch_youtube_transcript(url: str) -> str:
    """Fetch and extract the transcript from a youtube video."""
    generator = YoutubeTranscriptGenerator()
    return generator.get_transcript(url)
