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
        prompt = f"""IMPORTANT: YOUR ENTIRE RESPONSE MUST BE VALID JSON WITH NO OTHER TEXT.

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

YOUR RESPONSE MUST BE IN THIS EXACT JSON FORMAT WITH NOTHING ELSE:
{{
    "results": [
        {{
            "title": "The Actual Title of the Webpage",
            "url": "https://real-website.com/actual-page",
            "summary": "Actual summary of the content from the page..."
        }},
        ...
    ]
}}

DO NOT include any explanations, introductions, or notes outside the JSON structure.
DO NOT use markdown formatting around the JSON.
DO NOT write "```json" or any other text before or after the JSON.
YOUR ENTIRE RESPONSE SHOULD BE PARSEABLE AS JSON."""

        # Prepare the user message with topic and additional context if provided
        user_message = f"Search the web for information about: {topic}"
        if additional_context:
            user_message += f"\n\nAdditional context: {additional_context}"

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
            parsed_data = self._extract_results_from_text(content)
            references = parsed_data.get("results", [])

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

    def _extract_results_from_text(self, text: str) -> dict:
        """Extract structured results from the text response."""
        try:
            logger.debug(f"Parsing text as JSON: {text[:100]}...")

            # Try to find JSON content in the response
            json_start = text.find("{")
            json_end = text.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_content = text[json_start:json_end]
                # Parse the JSON content
                results = json.loads(json_content)
                return results
            else:
                logger.warning("No JSON object found in the response")
                return {"results": []}
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON: {e}")
            logger.debug(f"Response text: {text}")

            # Fall back to regex extraction if JSON parsing fails
            logger.warning("Falling back to regex-based extraction")
            regex_results = self._extract_results_with_regex(text)
            return {"results": regex_results}
