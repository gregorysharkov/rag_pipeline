import json
import logging
from typing import Any, Optional, Union

from openai import OpenAI

logger = logging.getLogger(__name__)


class LLMWrapper:
    """A unified wrapper for LLM interactions across the application."""

    def __init__(self, client: Optional[OpenAI] = None, default_model: str = "gpt-4"):
        """
        Initialize the LLM wrapper.

        Args:
            client: Optional OpenAI client instance. If not provided, will attempt to create one from environment.
            default_model: Default model to use for completions.
        """
        self.client = client or self._initialize_client()
        self.default_model = default_model

    @staticmethod
    def _initialize_client() -> OpenAI:
        """Initialize OpenAI client from environment variables."""
        try:
            return OpenAI()
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise

    def generate_completion(  # noqa: PLR0913
        self,
        system_prompt: str,
        user_message: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[dict[str, str]] = None,
        tools: Optional[list[dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, dict[str, str]]] = None,
    ) -> str:
        """
        Generate a completion using the OpenAI API.

        Args:
            system_prompt: The system prompt to guide the model's behavior
            user_message: The user's input message
            model: Optional model override. If not provided, uses default_model
            temperature: Controls randomness in the response (0.0 to 2.0)
            max_tokens: Maximum tokens in the response
            response_format: Optional format specification for the response
            tools: Optional list of tools/functions available to the model
            tool_choice: Optional specification for tool selection

        Returns:
            The generated completion text

        Raises:
            Exception: If the API call fails
        """
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ]

            # Build completion parameters
            params = {
                "model": model or self.default_model,
                "messages": messages,
                "temperature": temperature,
            }

            if max_tokens is not None:
                params["max_tokens"] = max_tokens
            if response_format is not None:
                params["response_format"] = response_format
            if tools is not None:
                params["tools"] = tools
            if tool_choice is not None:
                params["tool_choice"] = tool_choice

            logger.info(f"Generating completion with model: {params['model']}")
            response = self.client.chat.completions.create(**params)

            completion_text = response.choices[0].message.content
            logger.info("Successfully generated completion")

            return completion_text

        except Exception as e:
            logger.error(f"Error during completion generation: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            raise

    def generate_structured_completion(
        self,
        system_prompt: str,
        user_message: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
    ) -> dict[str, Any]:
        """
        Generate a completion that returns a JSON structure.

        Args:
            system_prompt: The system prompt to guide the model's behavior
            user_message: The user's input message
            model: Optional model override
            temperature: Controls randomness in the response

        Returns:
            Parsed JSON response as a dictionary
        """
        response = self.generate_completion(
            system_prompt=system_prompt,
            user_message=user_message,
            model=model,
            temperature=temperature,
            response_format={"type": "json_object"},
        )

        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise
