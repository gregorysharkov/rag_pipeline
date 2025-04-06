import json
import logging
import os
import re
import shutil
from typing import Any

from dotenv import load_dotenv
from llama_index.core import KnowledgeGraphIndex, SimpleDirectoryReader
from llama_index.core.settings import Settings
from llama_index.core.storage import StorageContext
from llama_index.llms.openai import OpenAI as LlamaOpenAI
from openai import OpenAI
from tqdm import tqdm

from web_app.backend.agents.researcher.graph_database import get_or_create_graph_store
from web_app.backend.agents.researcher.graph_store import DeduplicatingNeo4jGraphStore
from web_app.backend.agents.researcher.web_page_scraping import fetch_webpage_content
from web_app.backend.agents.web_search_agent import WebSearchAgent
from web_app.backend.session.session import ScriptSession
from web_app.logging.logger import setup_logging

# Load environment variables
load_dotenv()
# Configure logging
setup_logging()
logger = logging.getLogger(__name__)


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


def setup_web_search_agent() -> WebSearchAgent:
    return WebSearchAgent(
        client=OpenAI(api_key=os.getenv("OPENAI_API_KEY")),
    )


def setup_llm() -> LlamaOpenAI:
    return LlamaOpenAI(api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4")


def send_search_request(
    web_search_agent: WebSearchAgent,
    script_session: ScriptSession,
) -> list[dict[str, Any]]:
    logger.info("Running web search")
    search_results = web_search_agent.run(
        topic=script_session.topic,
        additional_context=script_session.additional_context,
    )
    logger.info(f"Found {len(search_results)} search results")
    return search_results


def create_temp_docs(search_results: list[dict[str, Any]]) -> None:
    # Create a temporary directory to store the search results as text files
    os.makedirs("temp_docs", exist_ok=True)
    logger.info("Created temporary directory for documents")


def setup_llama_index() -> None:
    # Initialize LlamaIndex components and graph store first
    logger.info("Initializing LlamaIndex components")
    Settings.llm = setup_llm()
    logger.info("Configured LLM settings")


def setup_storage_context() -> tuple[StorageContext, DeduplicatingNeo4jGraphStore]:  # type: ignore
    # Create a graph store
    logger.info("Creating graph store")
    graph_store = get_or_create_graph_store()
    storage_context = StorageContext.from_defaults(graph_store=graph_store)
    logger.info("Created storage context")
    return storage_context, graph_store


def process_search_results(
    search_results: list[dict[str, Any]],
    storage_context: StorageContext,
    graph_store: DeduplicatingNeo4jGraphStore,  # type: ignore
) -> KnowledgeGraphIndex:
    """Process search results and create knowledge graph."""
    # Save search results as text files with full content, skip if already exists
    skipped_docs = 0
    new_docs = 0

    # Create temp directory if it doesn't exist
    os.makedirs("temp_docs", exist_ok=True)

    for i, result in enumerate(search_results):
        url = result["url"]
        if graph_store.check_document_exists(url):
            logger.info(f"Skipping existing document: {result['title']}")
            skipped_docs += 1
            continue

        logger.info(
            f"Processing new search result {i + 1}/{len(search_results)}: {result['title']}"
        )
        try:
            content = fetch_webpage_content(result["url"])
            # Create document file
            doc_path = f"temp_docs/result_{i}.txt"
            with open(doc_path, "w") as f:
                f.write(f"Title: {result['title']}\n")
                f.write(f"URL: {result['url']}\n")
                f.write(f"Summary: {result['summary']}\n")
                f.write(f"Full Content:\n{content}\n")
            new_docs += 1
            logger.info(f"Saved document {i + 1} to {doc_path}")

            # Create Document node in Neo4j
            with graph_store.driver.session() as session:
                session.run(
                    """
                    MERGE (d:Document {url: $url})
                    SET d.title = $title,
                        d.summary = $summary,
                        d.content = $content,
                        d.created_at = datetime()
                """,
                    url=url,
                    title=result["title"],
                    summary=result["summary"],
                    content=content,
                )

        except Exception as e:
            logger.error(f"Error processing document {result['title']}: {str(e)}")
            continue

    logger.info(f"Skipped {skipped_docs} existing documents, processed {new_docs} new documents")

    if new_docs == 0:
        logger.warning("No new documents to process")
        return None

    # Load documents and create knowledge graph
    logger.info("Loading new documents")
    documents = SimpleDirectoryReader("temp_docs").load_data()
    logger.info(f"Loaded {len(documents)} new documents")

    logger.info("Creating knowledge graph")
    with tqdm(total=len(documents), desc="Processing documents") as pbar:
        kg_index = KnowledgeGraphIndex.from_documents(
            documents,
            storage_context=storage_context,
            include_embeddings=True,
            max_triplets_per_chunk=10,
            show_progress=True,
            progress_callback=lambda: pbar.update(1),
            embed_batch_size=10,
        )
    logger.info("Knowledge graph updated successfully")
    return kg_index


def query_key_ml_questions(kg_index) -> dict:
    """
    Query the knowledge graph for key machine learning project questions
    and format the response as a dictionary.
    """
    logger.info("Querying knowledge graph for key ML project questions")

    # More specific query that focuses on questions to answer when starting ML projects
    query = """
    What are the 10 most important questions that need to be addressed when starting a complex machine learning project? 
    Focus on questions about:
    1. Project scope and requirements
    2. Data collection and quality
    3. Model selection and architecture
    4. Infrastructure and deployment
    5. Performance metrics and evaluation
    6. Team and resource requirements
    7. Timeline and milestones
    8. Risk assessment and mitigation
    9. Maintenance and monitoring
    10. Cost considerations
    """

    query_engine = kg_index.as_query_engine()
    response = query_engine.query(query)

    # Convert the response text into a structured dictionary
    questions_dict = {}

    # Split the response into individual questions
    raw_questions = str(response).split("\n")

    for idx, question in enumerate(raw_questions, 1):
        # Clean up the question text (remove numbering if present)
        cleaned_question = question.strip()
        if cleaned_question:  # Skip empty lines
            # Remove common prefixes like "1.", "1)", "-", etc.
            cleaned_question = re.sub(r"^\d+[\.\)]\s*|-\s*", "", cleaned_question)
            cleaned_question = cleaned_question.strip()

            if cleaned_question:  # Only add non-empty questions
                questions_dict[f"q{idx}"] = {"question": cleaned_question}

    logger.info(f"Found {len(questions_dict)} key questions")
    return questions_dict


def collect_answers_to_questions(kg_index, questions_dict) -> dict:
    """Collect answers to questions from the knowledge graph."""
    query_engine = kg_index.as_query_engine()
    for question in questions_dict.values():
        response = query_engine.query(question["question"])
        question["answer"] = response.response
    return questions_dict


def main() -> None:
    script_session = setup_script_session()
    logger.info("Initializing WebSearchAgent")
    web_search_agent = setup_web_search_agent()

    search_results = send_search_request(web_search_agent, script_session)
    create_temp_docs(search_results)
    setup_llama_index()
    storage_context, graph_store = setup_storage_context()

    kg_index = process_search_results(search_results, storage_context, graph_store)

    results = query_key_ml_questions(kg_index)
    results = collect_answers_to_questions(kg_index, results)
    print(json.dumps(results, indent=4))  # noqa: T201
    # Clean up temporary files
    logger.info("Cleaning up temporary files")
    shutil.rmtree("temp_docs")
    logger.info("Temporary files removed")

    logger.info("Script completed successfully")


if __name__ == "__main__":
    main()
