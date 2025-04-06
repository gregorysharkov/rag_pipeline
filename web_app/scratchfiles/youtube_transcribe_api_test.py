import logging

from web_app.backend.agents.researcher.youtube_transcript_generator import (
    YoutubeTranscriptGenerator,
)
from web_app.logging.logger import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


def main():
    # Create transcript generator
    generator = YoutubeTranscriptGenerator()
    url = "https://www.youtube.com/watch?v=WWS4GnLJkaE"
    transcript = generator.get_transcript(url)
    logger.info(transcript)


if __name__ == "__main__":
    main()
