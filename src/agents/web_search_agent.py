import re
import datetime
import json
import logging
import os
from typing import Optional

from openai import OpenAI

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class WebSearchAgent(BaseAgent):
    """Agent responsible for performing web searches and retrieving references."""

    def __init__(self, client: OpenAI, debug_mode: bool = False):
        super().__init__(
            name="WebSearchAgent",
            model="gpt-4o-search-preview",  # Default to search-enabled model
            description="Performs web searches to find relevant references on a given topic.",
            client=client,
        )
        self.debug_mode = debug_mode
        self.debug_dir = "debug_outputs"

        # Create debug directory if in debug mode
        if self.debug_mode:
            os.makedirs(self.debug_dir, exist_ok=True)

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
                if self.debug_mode:
                    self._save_debug_output(
                        json.dumps(references, indent=2),
                        f"search_results_{topic.replace(' ', '_')[:30]}.json",
                    )
                return references
        except Exception as e:
            logger.error(f"Web search failed with error: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")

            # Try the direct approach without the agent wrapper
            try:
                logger.info("Trying direct API approach as fallback...")
                references = self._direct_search(topic, current_date, additional_context)
                if references:
                    logger.info(
                        f"Successfully retrieved {len(references)} references using direct API call"
                    )
                    if self.debug_mode:
                        self._save_debug_output(
                            json.dumps(references, indent=2),
                            f"direct_search_results_{topic.replace(' ', '_')[:30]}.json",
                        )
                    return references
            except Exception as direct_e:
                logger.error(f"Direct search fallback failed: {str(direct_e)}")
                logger.error(f"Error type: {type(direct_e).__name__}")
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
        
        YOU MUST RETURN THE RESULTS IN THE FOLLOWING JSON FORMAT:
        ```json
        [
          {{
            "title": "Title of the webpage",
            "url": "URL of the webpage",
            "summary": "Brief summary of the content"
          }},
          {{
            "title": "Title of the second webpage",
            "url": "URL of the second webpage",
            "summary": "Brief summary of the second content"
          }},
          ...
        ]
        ```
        
        DO NOT include any explanatory text or other formatting outside of the JSON structure.
        The response should be valid JSON that can be parsed directly.
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

            # Log the entire response structure for debugging
            logger.info(f"Response model: {response.model}")
            logger.info(f"Response ID: {response.id}")

            # Get and log raw content
            raw_content = response.choices[0].message.content
            logger.info(f"RAW CONTENT PREVIEW: {raw_content[:200]}...")

            # Save raw response if in debug mode
            if self.debug_mode:
                self._save_debug_output(
                    raw_content, f"raw_response_{topic.replace(' ', '_')[:30]}.txt"
                )

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

            # Parse as JSON
            try:
                references = self._parse_json_response(content)
                logger.info(
                    f"Successfully extracted {len(references)} references using JSON parser"
                )
            except Exception as json_e:
                logger.warning(f"JSON parsing failed: {str(json_e)}")
                logger.warning("Returning empty results as fallback")
                return []

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

    def _parse_json_response(self, text: str) -> list[dict[str, str]]:
        """Extract JSON from the response text."""
        logger.info("Parsing response as JSON")

        # Remove any markdown code block indicators
        text = re.sub(r"```json\s*", "", text)
        text = re.sub(r"```\s*", "", text)

        # Try to find JSON array pattern
        json_match = re.search(r"\[\s*\{.*\}\s*\]", text, re.DOTALL)
        if json_match:
            json_text = json_match.group(0)
            return json.loads(json_text)

        # If no JSON array found, try to parse the whole text
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning("Could not find valid JSON in the response")
            raise ValueError("Could not find valid JSON in the response")

    def _save_debug_output(self, content: str, filename: str) -> None:
        """Save debug output to file if in debug mode."""
        if not self.debug_mode:
            return

        try:
            filepath = os.path.join(self.debug_dir, filename)
            with open(filepath, "w") as f:
                f.write(content)
            logger.info(f"Debug output saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving debug output: {str(e)}")

    def _direct_search(
        self, topic: str, current_date: str, additional_context: Optional[str] = None
    ) -> list[dict[str, str]]:
        """Direct API call as fallback without the agent wrapper."""
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
        
        YOU MUST RETURN THE RESULTS IN THE FOLLOWING JSON FORMAT:
        ```json
        [
          {{
            "title": "Title of the webpage",
            "url": "URL of the webpage",
            "summary": "Brief summary of the content"
          }},
          {{
            "title": "Title of the second webpage",
            "url": "URL of the second webpage",
            "summary": "Brief summary of the second content"
          }},
          ...
        ]
        ```
        
        DO NOT include any explanatory text or other formatting outside of the JSON structure.
        The response should be valid JSON that can be parsed directly.
        """

        # Prepare the user message with topic and additional context if provided
        user_message = f"Search the web for information about: {topic}"
        if additional_context:
            user_message += f"\n\nAdditional context to guide the search: {additional_context}"

        logger.info(f"Making direct API call with model: {self.model}")

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

            # Save raw response if in debug mode
            if self.debug_mode:
                raw_content = response.choices[0].message.content
                self._save_debug_output(
                    raw_content, f"direct_raw_response_{topic.replace(' ', '_')[:30]}.txt"
                )

            # Process the response
            return self._process_response(response, topic)
        except Exception as e:
            logger.error(f"Error during direct API call: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
