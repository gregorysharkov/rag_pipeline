import concurrent.futures
import logging
import re
from abc import ABC, abstractmethod
from datetime import datetime

from web_app.backend.agents.commons.collected_information import CollectedInformation
from web_app.backend.agents.commons.common_search_instructions import (
    COMMON_SEARCH_INSTRUCTIONS,
)
from web_app.backend.agents.commons.web_page_scraping import (
    fetch_webpage_content,
    fetch_youtube_transcript,
)
from web_app.backend.session.session import ScriptSession
from web_app.logging.logger import setup_logging
from web_app.utils.openai_utils import extract_structured_response, get_openai_response

setup_logging()
logger = logging.getLogger(__name__)

current_date = datetime.now().strftime("%Y-%m-%d")


class InformationCollectorAgent(ABC):
    """Base class for all information collectors."""

    def __init__(self, script_session: ScriptSession, **kwargs):
        self.script_session = script_session
        self.__dict__.update(kwargs)
        self._items = None
        self.max_workers = 5  # Configurable number of workers

    @abstractmethod
    def collect_information(self) -> list[CollectedInformation]:
        """Collects information given the query and additional context."""
        pass

    @abstractmethod
    def process_items(self, items: list[CollectedInformation]) -> None:
        """Processes the response from the LLM and fills the content field."""
        pass

    def process_item_safe(self, item: CollectedInformation) -> None:
        """Safely process a single item with error handling."""
        try:
            item.fetch_content()
            logger.info(f"Successfully processed item: {item.title}")
        except Exception as e:
            logger.error(f"Error processing item {item.url}: {str(e)}")

    def process_items_parallel(self, items: list[CollectedInformation]) -> None:
        """Process items in parallel using ThreadPoolExecutor."""
        if not items:
            return

        logger.info(f"Processing {len(items)} items in parallel...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all items for processing
            futures = [executor.submit(self.process_item_safe, item) for item in items]

            # Wait for all futures to complete
            concurrent.futures.wait(futures)

        logger.info("Parallel processing completed")

    @property
    def collected_items(self) -> list[CollectedInformation]:
        """Get collected items, fetching them if necessary."""
        if self._items is None:
            self._items = self.collect_information()
            if self._items is not None:
                self.process_items_parallel(self._items)
        return self._items or []


class WebSearchCollectorAgent(InformationCollectorAgent):
    @property
    def user_message(self) -> str:
        return f"""
        You are a web search specialist with access to the latest information up to {current_date}.
        Your task is to search the web for the most relevant and up-to-date information on the given topic {self.script_session.topic}.
        ADDITIONAL CONTEXT: {self.script_session.additional_context}

        Return exactly from 5 to 10 high-quality search results that would be most helpful for someone creating content on this topic.
        """

    def collect_information(self) -> list[CollectedInformation]:
        response = get_openai_response(
            prompt=COMMON_SEARCH_INSTRUCTIONS,
            user_message=self.user_message,
            model=self.model,
            client=self.client,
        )

        content = response.choices[0].message.content
        response_list = extract_structured_response(content)
        if not response_list:
            return []

        logger.info(f"Collected {len(response_list)} web search results")
        return [
            CollectedInformation(
                title=item.get("title", ""),
                url=item.get("url", ""),
                summary=item.get("summary", ""),
                collector_func=fetch_webpage_content,
            )
            for item in response_list
        ]

    def process_items(self, items: list[CollectedInformation]) -> None:
        """Process web pages in parallel."""
        self.process_items_parallel(items)


class YoutubeSearchCollectorAgent(InformationCollectorAgent):
    """Agent responsible for collecting YouTube video information."""

    def __init__(self, script_session: ScriptSession, **kwargs):
        super().__init__(script_session, **kwargs)
        self.youtube_url_patterns = [
            r"(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})",
            r"(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})",
        ]
        self.max_workers = 3  # Limit concurrent YouTube API calls

    @property
    def user_message(self):
        return f"""
        You are a YouTube search specialist with access to the latest information up to {current_date}.
        Your task is to find the most relevant and high-quality YouTube videos about: {self.script_session.topic}
        Additional context to consider: {self.script_session.additional_context}

        IMPORTANT REQUIREMENTS:
        1. Return ONLY YouTube video URLs (no other websites)
        2. Each URL must be in one of these formats:
           - https://www.youtube.com/watch?v=VIDEO_ID
           - https://youtu.be/VIDEO_ID
        3. Videos should be:
           - From reputable creators
           - Recent (preferably within the last 2 years)
           - In English or with English subtitles
           - Relevant to the topic
        4. Return 3-5 high-quality results (quality over quantity)
        5. The video duration should be between 10 and 30 minutes

        For each video, provide:
        1. The exact title of the YouTube video
        2. The complete YouTube URL
        3. A brief summary of the video content (2-3 sentences)

        The viceo ids should be real, not generic `VIDEO_ID`
        """

    def _is_valid_youtube_url(self, url: str) -> bool:
        """Validate if the URL is a proper YouTube video URL."""
        if not url:
            return False

        # Check if URL matches any of our YouTube patterns
        return any(re.match(pattern, url) for pattern in self.youtube_url_patterns)

    def collect_information(self) -> list[CollectedInformation]:
        """Collect information about relevant YouTube videos."""
        response = get_openai_response(
            prompt=COMMON_SEARCH_INSTRUCTIONS,
            user_message=self.user_message,
            model=self.model,
            client=self.client,
        )

        content = response.choices[0].message.content
        response_list = extract_structured_response(content)

        if not response_list:
            return []

        # Filter and validate YouTube URLs
        valid_items = []
        for item in response_list:
            url = item.get("url", "")
            if self._is_valid_youtube_url(url):
                valid_items.append(
                    CollectedInformation(
                        title=item.get("title", ""),
                        url=url.strip("'\""),
                        summary=item.get("summary", ""),
                        collector_func=fetch_youtube_transcript,
                    )
                )
            else:
                logger.warning(f"Skipping invalid YouTube URL: {url}")

        logger.info(f"Collected {len(valid_items)} valid YouTube videos")
        return valid_items

    def process_items(self, items: list[CollectedInformation]) -> None:
        """Process collected YouTube videos by fetching their transcripts in parallel."""
        self.process_items_parallel(items)
