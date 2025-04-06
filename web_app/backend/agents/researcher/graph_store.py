import hashlib
import logging
from typing import Any

from llama_index.graph_stores.neo4j import Neo4jGraphStore
from neo4j import GraphDatabase

from web_app.backend.agents.researcher.constants import NEO4J_PASSWORD, NEO4J_URI, NEO4J_USER

logger = logging.getLogger(__name__)


class DeduplicatingNeo4jGraphStore(Neo4jGraphStore):
    """Custom Neo4j graph store with deduplication and update logic."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize the driver after super().__init__ to ensure url is set
        self.driver = GraphDatabase.driver(
            kwargs.get("url", NEO4J_URI),
            auth=(kwargs.get("username", NEO4J_USER), kwargs.get("password", NEO4J_PASSWORD)),
        )

    def _create_constraints(self):
        """Create constraints for deduplication."""
        with self.driver.session() as session:
            # Create unique constraint on URL for documents
            session.run("""
                CREATE CONSTRAINT document_url IF NOT EXISTS
                FOR (n:Document) REQUIRE n.url IS UNIQUE
            """)

            # Create unique constraint on text hash for nodes
            session.run("""
                CREATE CONSTRAINT node_text_hash IF NOT EXISTS
                FOR (n:Node) REQUIRE n.text_hash IS UNIQUE
            """)

    def _compute_text_hash(self, text: str) -> str:
        """Compute a hash of the text for deduplication."""
        return hashlib.md5(text.encode()).hexdigest()

    def _merge_node(self, session, node_data: dict[str, Any]) -> str:
        """Merge a node with deduplication logic."""
        text_hash = self._compute_text_hash(node_data.get("text", ""))

        # Try to find existing node with similar content
        result = session.run(
            """
            MATCH (n:Node)
            WHERE n.text_hash = $text_hash
            RETURN n
        """,
            text_hash=text_hash,
        )

        existing_node = result.single()

        if existing_node:
            # Update existing node
            session.run(
                """
                MATCH (n:Node {text_hash: $text_hash})
                SET n += $properties,
                    n.updated_at = datetime()
                RETURN n
            """,
                text_hash=text_hash,
                properties=node_data,
            )
            return existing_node["n"].id

        # Create new node
        result = session.run(
            """
            CREATE (n:Node)
            SET n += $properties,
                n.created_at = datetime(),
                n.updated_at = datetime()
            RETURN n
        """,
            properties={**node_data, "text_hash": text_hash},
        )

        return result.single()["n"].id

    def _merge_relationship(
        self, session, rel_data: dict[str, Any], source_id: str, target_id: str
    ) -> None:
        """Merge a relationship with deduplication logic."""
        session.run(
            """
            MATCH (source:Node {id: $source_id})
            MATCH (target:Node {id: $target_id})
            MERGE (source)-[r:RELATES_TO]->(target)
            SET r += $properties,
                r.updated_at = datetime()
        """,
            source_id=source_id,
            target_id=target_id,
            properties=rel_data,
        )

    def add_graph(self, nodes: list[dict[str, Any]], relationships: list[dict[str, Any]]) -> None:
        """Add nodes and relationships with deduplication."""
        with self.driver.session() as session:
            # Create constraints if they don't exist
            self._create_constraints()

            # Process nodes
            node_ids = {}
            for node in nodes:
                node_id = self._merge_node(session, node)
                node_ids[node.get("id")] = node_id

            # Process relationships
            for rel in relationships:
                source_id = node_ids.get(rel.get("source"))
                target_id = node_ids.get(rel.get("target"))
                if source_id and target_id:
                    self._merge_relationship(session, rel, source_id, target_id)

    def check_document_exists(self, url: str) -> bool:
        """Check if a document with the given URL already exists."""
        try:
            with self.driver.session() as session:
                result = session.run(
                    """
                    OPTIONAL MATCH (n:Document {url: $url})
                    RETURN count(n) as count
                """,
                    url=url,
                )
                return result.single()["count"] > 0
        except Exception as e:
            logger.debug(
                f"Error checking document existence (this is normal for first run): {str(e)}"
            )
            return False
