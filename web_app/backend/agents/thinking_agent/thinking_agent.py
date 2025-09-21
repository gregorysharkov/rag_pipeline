import logging
from dataclasses import dataclass

from web_app.backend.agents.commons.knowledge_graph_manager import KnowledgeGraphManager
from web_app.backend.agents.research_agent.researcher_agent import ContextResearcherAgent
from web_app.backend.session.session import ScriptSession
from web_app.logging.logger import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


@dataclass
class ScriptConcept:
    title: str
    hook: str
    description: str
    value_proposition: str
    key_questions: list[str]


class ThinkingAgent:
    """
    The agent thinks about the video concepts and makes
    sure that the existing knowledge graph contains the
    most relevant information.

    It is also responsible for generating the script concept
    after the relevant information is collected.
    """

    def __init__(
        self,
        script_session: ScriptSession,
        knowledge_graph_manager: KnowledgeGraphManager,
        researcher_agent: ContextResearcherAgent,
    ) -> None:
        self.script_session = script_session
        self.kg_manager = knowledge_graph_manager
        self.researcher_agent = researcher_agent

    def generate_video_concepts(self):
        """
        Generates 2-3 high-level video concepts based on the topic and target audience.
        Each concept includes:
        - Title: The title of the video
        - Description: A short description of the video
        - Hook: How to grab viewer attention
        - Value Proposition: Why viewers should care
        - Key Questions: What the video will answer
        """

    def analyze_questions(self, concept_questions):
        """
        For each concept's questions:
        1. Query knowledge graph
        2. Evaluate answer quality
        3. Identify knowledge gaps
        """

    def fill_knowledge_gaps(self, concept_questions):
        """
        Uses researcher_agent to gather missing information
        """

    def evaluate_concepts(self, concepts_with_answers):
        """
        Scores each concept based on:
        - Answer completeness
        - Topic coherence
        - Audience alignment
        - Hook strength
        """

    def select_best_concept(self):
        """
        Picks the most promising concept based on evaluation
        """
