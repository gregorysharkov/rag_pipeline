import logging
import os
from datetime import datetime
from typing import Optional

from llama_index.core import Document, KnowledgeGraphIndex
from llama_index.core.settings import Settings
from llama_index.core.storage import StorageContext
from llama_index.llms.openai import OpenAI as LlamaOpenAI
from neo4j import Session
from tqdm import tqdm

from web_app.backend.agents.researcher.collected_information import CollectedInformation
from web_app.backend.agents.researcher.graph_database import get_or_create_graph_store
from web_app.backend.agents.researcher.graph_store import DeduplicatingNeo4jGraphStore
from web_app.logging.logger import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


class KnowledgeGraphManager:
    """Manages the transformation and updating of the knowledge graph."""

    def __init__(self, llm: Optional[LlamaOpenAI] = None):
        """Initialize the KnowledgeGraphManager.

        Args:
            llm: Optional LlamaOpenAI instance. If not provided, a default one will be created.
        """
        self.llm = llm or LlamaOpenAI(api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4")
        Settings.llm = self.llm
        self.storage_context, self.graph_store = self._setup_storage_context()
        self.kg_index = self._load_existing_knowledge_graph()

    def _setup_storage_context(self) -> tuple[StorageContext, DeduplicatingNeo4jGraphStore]:
        """Set up the storage context and graph store."""
        logger.info("Creating graph store")
        graph_store = get_or_create_graph_store()
        storage_context = StorageContext.from_defaults(graph_store=graph_store)
        logger.info("Created storage context")
        return storage_context, graph_store

    def _load_existing_knowledge_graph(self) -> KnowledgeGraphIndex:
        """Load the existing knowledge graph from Neo4j.

        Returns:
            Existing KnowledgeGraphIndex
        """
        logger.info("Loading existing knowledge graph")
        try:
            # Get all existing documents from Neo4j
            with self.graph_store.driver.session() as session:
                result = session.run(
                    """
                    MATCH (d:Document)
                    RETURN d.title as title, d.url as url, d.summary as summary, 
                           d.content as content, d.created_at as created_at
                    """
                )
                documents = []
                for record in result:
                    # Create Document objects for existing documents
                    text = (
                        f"Title: {record['title']}\n"
                        f"URL: {record['url']}\n"
                        f"Summary: {record['summary']}\n"
                        f"Content: {record['content']}"
                    )
                    doc = Document(
                        text=text,
                        metadata={
                            "title": record["title"],
                            "url": record["url"],
                            "summary": record["summary"],
                            "created_at": record["created_at"].isoformat()
                            if record["created_at"]
                            else datetime.now().isoformat(),
                        },
                    )
                    documents.append(doc)

            logger.info(f"Found {len(documents)} existing documents")

            # Create index with existing documents
            if documents:
                kg_index = KnowledgeGraphIndex.from_documents(
                    documents,
                    storage_context=self.storage_context,
                    include_embeddings=True,
                    max_triplets_per_chunk=10,
                )
            else:
                # If no documents exist, create empty index
                kg_index = KnowledgeGraphIndex([], storage_context=self.storage_context)

            logger.info("Successfully loaded existing knowledge graph")
            return kg_index

        except Exception as e:
            logger.error(f"Error loading existing knowledge graph: {str(e)}")
            # Create empty index if loading fails
            logger.warning("Creating empty knowledge graph")
            return KnowledgeGraphIndex([], storage_context=self.storage_context)

    def _merge_document_to_graph(self, session: Session, item: CollectedInformation) -> None:
        """Merge a document into the Neo4j graph.

        Args:
            session: Neo4j session
            item: CollectedInformation item to merge
        """
        session.run(
            """
            MERGE (d:Document {url: $url})
            SET d.title = $title,
                d.summary = $summary,
                d.content = $content,
                d.created_at = datetime()
            """,
            url=item.url,
            title=item.title,
            summary=item.summary,
            content=item.content,
        )

    def _create_llama_document(self, item: CollectedInformation) -> Document:
        """Create a LlamaIndex Document from a CollectedInformation item.

        Args:
            item: CollectedInformation item

        Returns:
            LlamaIndex Document
        """
        # Combine metadata and content in a structured way
        text = (
            f"Title: {item.title}\n"
            f"URL: {item.url}\n"
            f"Summary: {item.summary}\n"
            f"Content: {item.content}"
        )

        # Create document with metadata
        return Document(
            text=text,
            metadata={
                "title": item.title,
                "url": item.url,
                "summary": item.summary,
                "created_at": datetime.now().isoformat(),
            },
        )

    def update_knowledge_graph(
        self, items: list[CollectedInformation]
    ) -> Optional[KnowledgeGraphIndex]:
        """Update the knowledge graph with new items.

        Args:
            items: list of CollectedInformation items to add to the knowledge graph

        Returns:
            Updated KnowledgeGraphIndex or None if no new items were processed
        """
        # Filter out items that already exist in the graph
        new_items = []
        for item in items:
            if not self.graph_store.check_document_exists(item.url):
                new_items.append(item)
            else:
                logger.info(f"Skipping existing document: {item.title}")

        if not new_items:
            logger.warning("No new documents to process")
            return self.kg_index

        # Create Document nodes in Neo4j
        with self.graph_store.driver.session() as session:
            for item in new_items:
                self._merge_document_to_graph(session, item)

        # Convert items to LlamaIndex Documents
        documents = [self._create_llama_document(item) for item in new_items]
        logger.info(f"Created {len(documents)} LlamaIndex documents")

        # Update existing knowledge graph with new documents
        logger.info("Updating knowledge graph with new documents")
        with tqdm(total=len(documents), desc="Processing documents") as pbar:
            for document in documents:
                self.kg_index.insert(document)
                pbar.update(1)

        # Persist the updated graph
        self.kg_index.storage_context.persist()
        logger.info("Knowledge graph updated and persisted successfully")

        return self.kg_index

    def get_knowledge_graph(self) -> KnowledgeGraphIndex:
        """Get the current knowledge graph.

        Returns:
            Current KnowledgeGraphIndex
        """
        return self.kg_index


def main() -> None:
    """Demonstrate proper usage of KnowledgeGraphManager."""
    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Create some sample CollectedInformation objects
    sample_items = [
        CollectedInformation(
            title="Understanding Machine Learning Complexity",
            url="https://example.com/ml-complexity",
            summary="A comprehensive guide to understanding and managing complexity in ML projects",
            content="Machine learning projects come with inherent complexity...",
        ),
        CollectedInformation(
            title="Best Practices in AI Development",
            url="https://example.com/ai-best-practices",
            summary="Key best practices for developing robust AI systems",
            content="When developing AI systems, following established best practices...",
        ),
    ]

    try:
        # Initialize the manager
        logger.info("Initializing KnowledgeGraphManager")
        kg_manager = KnowledgeGraphManager()

        # Update the knowledge graph with new items
        logger.info("Updating knowledge graph with sample items")
        kg_index = kg_manager.update_knowledge_graph(sample_items)

        if kg_index:
            # Demonstrate querying the knowledge graph
            logger.info("Querying the knowledge graph")
            query_engine = kg_index.as_query_engine()
            response = query_engine.query(
                "What are the key points about managing complexity in machine learning?"
            )
            logger.info(f"Query response: {response}")

            # Get the current state of the knowledge graph
            _current_graph = kg_manager.get_knowledge_graph()
            logger.info("Successfully retrieved current knowledge graph")

    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        raise


if __name__ == "__main__":
    main()
