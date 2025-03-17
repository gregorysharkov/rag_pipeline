import re
import datetime
import json
import logging
from typing import Optional

from openai import OpenAI

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class WebSearchAgent(BaseAgent):
    """Agent responsible for performing web searches and retrieving references."""

    def __init__(self, client: OpenAI):
        super().__init__(
            name="WebSearchAgent",
            model="gpt-4o-search-preview",  # Default to search-enabled model
            description="Performs web searches to find relevant references on a given topic.",
            client=client,
        )

    def run(self, topic: str, additional_context: Optional[str] = None) -> list[dict[str, str]]:
        """
        Perform a web search on the given topic and return top 5 references.
        If web search fails, falls back to generating plausible references.

        Args:
            topic: The topic to search for
            additional_context: Optional additional context to guide the search

        Returns:
            List of dictionaries containing reference information (title, url, summary)
        """
        logger.info(f"Performing web search for topic: {topic}")
        if additional_context:
            logger.info("Additional context provided to guide the search")

        # Current date for context
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")

        # First try with web search capability
        try:
            logger.info("Attempting to use web search capability...")
            references = self._search_web(topic, current_date, additional_context)
            if references:
                logger.info(f"Successfully retrieved {len(references)} references using web search")
                return references
        except Exception as e:
            logger.error(f"Web search failed with error: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")

        # If we get here, web search failed or returned no results, so fall back to generation
        logger.warning("Web search failed or returned no results")
        return []

    def _search_web(
        self, topic: str, current_date: str, additional_context: Optional[str] = None
    ) -> list[dict[str, str]]:
        """Perform a real web search using the search-enabled model."""
        prompt = f"""
        You are a web search specialist with access to the latest information up to {current_date}.
        Your task is to search the web for the most relevant and up-to-date information on the given topic.
        Return exactly 5 high-quality search results that would be most helpful for someone creating content on this topic.

        For each result, provide:
        1. A title - use the actual title from the webpage
        2. The URL - use the actual URL of the webpage, never create fictional URLs
        3. A brief summary of the content (100-150 words) based on the actual content of the page

        IMPORTANT:
        - Only return results from real websites that you've actually found through search
        - Do not generate fictional or example results
        - Do not use example.com or any placeholder domains
        - Ensure all URLs are from legitimate websites
        - If you cannot find enough results, return fewer than 5 rather than making up results
        
        Format each result as follows:
        
        ## Result 1
        Title: [Title of the webpage]
        URL: [URL of the webpage]
        Summary: [Brief summary of the content]
        
        ## Result 2
        ...and so on
        """

        # Prepare the user message with topic and additional context if provided
        user_message = f"Search the web for information about: {topic}"
        if additional_context:
            user_message += f"\n\nAdditional context to guide the search: {additional_context}"

        logger.info(f"Using model: {self.model}")
        logger.info(f"Sending search request for topic: {topic}")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": prompt,
                    },
                    {"role": "user", "content": user_message},
                ],
            )

            logger.info("Search request successful")
            logger.info(f"Response model: {response.model}")
            logger.info(f"Response ID: {response.id}")

            # Process the response
            return self._process_response(response, topic)
        except Exception as e:
            logger.error(f"Error during API call: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def _process_response(self, response, topic: str) -> list[dict[str, str]]:
        """Process the API response and extract references."""
        try:
            # Extract the content
            content = response.choices[0].message.content
            logger.info(f"Raw response content: {content[:100]}...")  # Log first 100 chars

            # Extract structured data from the text response
            references = self._extract_results_from_text(content)

            # Format and filter the references
            formatted_references = []
            for ref in references[:5]:  # Limit to 5 references
                # Validate the URL to ensure it's not from example.com or other placeholder domains
                url = ref.get("url", "")
                if not url or "example.com" in url or "placeholder" in url:
                    # Skip invalid URLs
                    logger.warning(f"Skipping reference with invalid URL: {url}")
                    continue

                formatted_ref = {
                    "title": ref.get("title", "Untitled"),
                    "url": url,
                    "summary": ref.get("summary", "No summary available"),
                }
                formatted_references.append(formatted_ref)

            return formatted_references
        except Exception as e:
            logger.error(f"Error processing response: {e}")
            return []

    def _extract_results_from_text(self, text: str) -> list[dict[str, str]]:
        """Extract structured results from the text response."""
        results = []

        # Try to find results using regex pattern matching
        # Look for sections that start with "## Result" or just "Result"
        result_sections = re.split(r"##\s*Result\s+\d+", text)

        # Remove the first section if it's empty or just introductory text
        if result_sections and (
            not result_sections[0].strip() or "below are" in result_sections[0].lower()
        ):
            result_sections = result_sections[1:]

        # If we couldn't split by "## Result", try another approach
        if len(result_sections) <= 1:
            # Try to split by numbered items or other formats
            result_sections = re.split(r"Result\s+\d+:|^\d+\.\s+", text, flags=re.MULTILINE)
            # Remove the first section if it's empty or introductory
            if result_sections and (
                not result_sections[0].strip() or "below are" in result_sections[0].lower()
            ):
                result_sections = result_sections[1:]

        for section in result_sections:
            if not section.strip():
                continue

            result = {}

            # Extract title - handle both "Title:" and "**Title:**" formats
            title_match = re.search(
                r"\*?\*?Title:?\*?\*?\s*(?:\*?\*?)?(.*?)(?:\*?\*?)?\s*(?:\n|$)",
                section,
                re.IGNORECASE,
            )
            if not title_match:
                # Try to find quoted title
                title_match = re.search(r'\*?\*?"([^"]+)"', section)

            if title_match:
                result["title"] = title_match.group(1).strip().strip('"')

            # Extract URL - handle both "URL:" and "**URL:**" formats
            url_match = re.search(
                r"\*?\*?URL:?\*?\*?\s*(?:\*?\*?)?(.*?)(?:\*?\*?)?\s*(?:\n|$)",
                section,
                re.IGNORECASE,
            )
            if not url_match:
                # Try to find a URL directly
                url_match = re.search(r"https?://[^\s\n]+", section)

            if url_match:
                result["url"] = (
                    url_match.group(1).strip()
                    if ":" in url_match.group(0)
                    else url_match.group(0).strip()
                )

            # Extract summary - handle both "Summary:" and "**Summary:**" formats
            summary_match = re.search(
                r"\*?\*?Summary:?\*?\*?\s*(?:\*?\*?)?(.*?)(?:\n\n|\n##|$)",
                section,
                re.DOTALL | re.IGNORECASE,
            )
            if summary_match:
                result["summary"] = summary_match.group(1).strip()
            elif "title" in result or "url" in result:
                # If we have a title or URL but no explicit summary, use the remaining text
                # Remove the title and URL parts from the section
                remaining_text = section
                if "title" in result:
                    remaining_text = re.sub(
                        r"\*?\*?Title:?\*?\*?\s*(?:\*?\*?)?.*?(?:\*?\*?)?\s*\n",
                        "",
                        remaining_text,
                        flags=re.IGNORECASE,
                    )
                if "url" in result:
                    remaining_text = re.sub(
                        r"\*?\*?URL:?\*?\*?\s*(?:\*?\*?)?.*?(?:\*?\*?)?\s*\n",
                        "",
                        remaining_text,
                        flags=re.IGNORECASE,
                    )
                # Clean up the remaining text
                remaining_text = remaining_text.strip()
                if remaining_text:
                    result["summary"] = remaining_text

            # Only add if we have at least a title or URL
            if result.get("title") or result.get("url"):
                # Clean up any remaining ** markers
                for key in result:
                    if isinstance(result[key], str):
                        result[key] = result[key].replace("**", "").strip()

                results.append(result)

        # If we still couldn't extract results, try a more general approach
        if not results:
            # Look for URLs in the text
            urls = re.findall(r"https?://[^\s\n]+", text)
            for url in urls:
                # Find the surrounding text (up to 500 chars before and after)
                start = max(0, text.find(url) - 500)
                end = min(len(text), text.find(url) + len(url) + 500)
                context = text[start:end]

                # Try to extract a title (text before the URL)
                title_match = re.search(
                    r'"([^"]+)".*?' + re.escape(url), context, re.DOTALL
                ) or re.search(r"([^\n.!?]+).*?" + re.escape(url), context, re.DOTALL)
                title = title_match.group(1).strip() if title_match else "Unknown Title"

                # Try to extract a summary (text after the URL)
                summary_match = re.search(
                    re.escape(url) + r".*?([^\n]+\n[^\n]+)", context, re.DOTALL
                )
                summary = (
                    summary_match.group(1).strip() if summary_match else "No summary available"
                )

                results.append({"title": title, "url": url, "summary": summary})

        return results
