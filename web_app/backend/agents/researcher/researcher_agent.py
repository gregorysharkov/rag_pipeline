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

import concurrent.futures
import logging
import os
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
from llama_index.core import KnowledgeGraphIndex
from openai import OpenAI

from web_app.backend.agents.researcher.collected_information import CollectedInformation
from web_app.backend.agents.researcher.information_collector_agents import (
    WebSearchCollectorAgent,
    YoutubeSearchCollectorAgent,
)
from web_app.backend.agents.researcher.knowledge_graph_manager import KnowledgeGraphManager
from web_app.backend.session.session import ScriptSession
from web_app.logging.logger import setup_logging

current_date = datetime.now().strftime("%Y-%m-%d")
setup_logging()
logger = logging.getLogger(__name__)


class ContextResearcherAgent:
    """Agent responsible for researching web information and maintaining the knowledge graph."""

    script_session: ScriptSession
    client: OpenAI
    model: str

    def __init__(self, script_session: ScriptSession, **kwargs):
        self.script_session = script_session
        self.__dict__.update(kwargs)

        # Initialize collector agents
        self.collector_agents = [
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

        # Initialize knowledge graph manager
        self.knowledge_graph_manager = KnowledgeGraphManager()

    def process_agents_parallel(self) -> list[CollectedInformation]:
        """Process all agents in parallel."""
        collected_items = []
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=len(self.collector_agents)
        ) as executor:
            # Submit all agents for processing
            future_to_agent = {
                executor.submit(lambda a: a.collected_items, agent): agent
                for agent in self.collector_agents
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

    def update_knowledge_graph(self) -> Optional[KnowledgeGraphIndex]:
        """Update the knowledge graph with newly collected items."""
        items = self.collected_items
        if not items:
            logger.warning("No items collected to update knowledge graph")
            return self.knowledge_graph_manager.get_knowledge_graph()

        logger.info(f"Updating knowledge graph with {len(items)} items")
        return self.knowledge_graph_manager.update_knowledge_graph(items)

    def query_knowledge_graph(self, query: str) -> str:
        """Query the knowledge graph.

        Args:
            query: The query to run against the knowledge graph

        Returns:
            Response from the knowledge graph
        """
        kg_index = self.knowledge_graph_manager.get_knowledge_graph()
        query_engine = kg_index.as_query_engine()
        response = query_engine.query(query)
        return str(response)

    def run(self) -> None:
        """Run the complete research process."""
        # Collect items from all sources
        items = self.collected_items
        logger.info(f"Collected {len(items)} items from all sources")

        # Update knowledge graph with new items
        kg_index = self.update_knowledge_graph()
        if kg_index:
            logger.info("Successfully updated knowledge graph")
        else:
            logger.warning("No updates made to knowledge graph")

        # Log collected items for debugging
        for item in items:
            logger.info(item)

    def dump_collected_items(self, base_path: str) -> None:
        """Dump all collected items to files."""
        for item in self.collected_items:
            item.dump_string(base_path)


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

    # Run the complete research process
    researcher_agent.run()

    # Example of querying the knowledge graph
    try:
        response = researcher_agent.query_knowledge_graph(
            "What are the key challenges in managing complex ML projects?"
        )
        logger.info(f"Knowledge graph query response: {response}")
    except ValueError as e:
        logger.error(f"Error querying knowledge graph: {str(e)}")

    # Save collected items
    researcher_agent.dump_collected_items("collected_items")


if __name__ == "__main__":
    main()
