"""
This researcher angent is responsible for researching the web information related to the user's query.
The research is performed to collect and analyze information to plan and create a youtube video script.

The process is as follows:
Part 1: Web search
1. The user provides a query and additional context to the agent.
2. The agent performs web search to find relevant information.
3. The agent collects text of the web pages provided in the web search.
4. The agent performs a youtube search to find relevant videos.
5. The processed videos are transcribed and the text is added to the context.
(5a) TODO: the agent should also be able to evaluate the relevance of the texts collected from the videos.

Part 2: Knowledge graph
1. The agent creates a knowledge graph of the collected information.

Part 3: Questions:
1. Before checking the graph, the agent thinks about the most important questions that a youtube video should answer.
2. The agent checks the graph to find the most relevant information to the questions.
"""

import json
import logging
import os
import re
import asyncio
import concurrent.futures
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional, List
from functools import partial

from dotenv import load_dotenv
from openai import OpenAI
from propcache import cached_property

from web_app.backend.agents.researcher.common_search_instructions import COMMON_SEARCH_INSTRUCTIONS
from web_app.backend.agents.researcher.web_page_scraping import (
    fetch_webpage_content,
    fetch_youtube_transcript,
)
from web_app.backend.session.session import ScriptSession
from web_app.logging.logger import setup_logging
from web_app.utils.openai_utils import extract_structured_response, get_openai_response

current_date = datetime.now().strftime("%Y-%m-%d")
setup_logging()
logger = logging.getLogger(__name__)


@dataclass
class CollectedInformation:
    title: str
    url: str
    summary: str
    collector_func: Callable
    content: Optional[str] = None

    def fetch_content(self) -> str:
        self.content = self.collector_func(self.url)

    def __str__(self) -> str:
        return (
            f"Collected_item\n"
            f"\tTitle: {self.title}\n"
            f"\tURL: {self.url}\n"
            f"\tSummary: {self.summary}\n"
            f"\tContent: {self.content[:100]}...\n"
        )

    def _generate_file_name(self, title: str) -> str:
        file_name = title.lower()
        file_name = re.sub(r"[^a-z0-9]+", " ", file_name)
        file_name = re.sub(r"\s+", "_", file_name)
        max_len = 30
        file_name = file_name[: min(len(file_name), max_len)]
        return file_name

    def dumps(self, base_path: str) -> None:
        file_name = self._generate_file_name(self.title)
        with open(f"{base_path}/{file_name}.txt", "w") as f:
            f.write(str(self))

    def dump_json(self, base_path: str) -> None:
        file_name = self._generate_file_name(self.title)
        with open(f"{base_path}/{file_name}.json", "w") as f:
            json.dump(self, f)


class ContextResearcherAgent:
    script_session: ScriptSession
    client: OpenAI
    model: str

    def __init__(self, script_session: ScriptSession, **kwargs):
        self.script_session = script_session
        self.__dict__.update(kwargs)
        self.agents = [
            WebSearchCollectorAgent(
                script_session=self.script_session,
                model=self.model,
                client=self.client,
            ),
            YoutubeSearchCollectorAgent(
                script_session=self.script_session,
                model=self.model,
                client=self.client,
            ),
        ]

    def process_agents_parallel(self) -> list[CollectedInformation]:
        """Process all agents in parallel."""
        collected_items = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.agents)) as executor:
            # Submit all agents for processing
            future_to_agent = {
                executor.submit(lambda a: a.collected_items, agent): agent for agent in self.agents
            }

            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_agent):
                agent = future_to_agent[future]
                try:
                    items = future.result()
                    collected_items.extend(items)
                except Exception as e:
                    logger.error(f"Error processing agent {type(agent).__name__}: {str(e)}")

        return collected_items

    @property
    def collected_items(self) -> list[CollectedInformation]:
        """Get all collected items from all agents in parallel."""
        return self.process_agents_parallel()

    def run(self) -> None:
        """Run the research process."""
        items = self.collected_items
        for item in items:
            logger.info(item)

    def dump_collected_items(self, base_path: str) -> None:
        """Dump all collected items to files."""
        for item in self.collected_items:
            item.dumps(base_path)


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


def setup_script_session() -> ScriptSession:
    script_session = ScriptSession(
        topic="Secrets of complex machine learning projects",
        additional_context="""
    I want to create an expert-level video focusing on how to build complex machine learning projects.

    Questions to answer:
    - How to measure complexity of a machine learning project?
    - What are the key ingredients of a complex machine learning project?
    - What are the next steps after building a POC / MVP?

    My thoughts on the topic:
    - Machine learning project is a software engineering project.
    - No ML project is built in a day, it is an iterative process, so version control is a must.
    - special focus on building a data cleaning pipeline (garbage in, garbage out).
    - special focus on building a feature store, because over the time you will be adding more and more features, some of them will be usefull some not.
    - special focus on building model training pipeline. Once you add or remove features, you need to retrain the model.
    - special focus on expreiment tracking and model registry.
    """,
        target_audience="Professionals",
        content_type="Explainer",
        tone="Conversational",
        use_web_search=True,
    )
    return script_session


def main():
    load_dotenv()
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    model = "gpt-4o-search-preview"

    script_session = setup_script_session()
    researcher_agent = ContextResearcherAgent(script_session, model=model, client=openai_client)
    researcher_agent.run()
    researcher_agent.dump_collected_items("collected_items")


if __name__ == "__main__":
    main()
