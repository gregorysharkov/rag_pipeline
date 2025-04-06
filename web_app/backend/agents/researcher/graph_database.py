import logging

from neo4j import GraphDatabase

from web_app.backend.agents.researcher.constants import NEO4J_PASSWORD, NEO4J_URI, NEO4J_USER
from web_app.backend.agents.researcher.graph_store import DeduplicatingNeo4jGraphStore

logger = logging.getLogger(__name__)


def get_or_create_graph_store() -> DeduplicatingNeo4jGraphStore:
    """Get or create a Neo4j graph store with deduplication."""
    try:
        # Test connection
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        driver.verify_connectivity()
        driver.close()

        logger.info("Connected to existing Neo4j database")
        return DeduplicatingNeo4jGraphStore(
            username=NEO4J_USER, password=NEO4J_PASSWORD, url=NEO4J_URI, database="neo4j"
        )
    except Exception as e:
        logger.error(f"Error connecting to Neo4j: {str(e)}")
        logger.info("Please ensure Neo4j is running using: docker-compose up -d")
        raise
