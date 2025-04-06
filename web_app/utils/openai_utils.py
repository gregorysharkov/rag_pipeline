import json
import logging

from openai import OpenAI

from web_app.logging.logger import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


def get_openai_response(prompt: str, user_message: str, model: str, client: OpenAI) -> str:
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": prompt,
                },
                {"role": "user", "content": user_message},
            ],
        )
        return response
    except Exception as e:
        logger.error(f"Error getting OpenAI response: {e}")
        raise e


def extract_structured_response(text: str) -> dict:
    """convert the text response to a structured JSON object"""
    json_start = text.find("{")
    json_end = text.rfind("}") + 1

    if json_start >= 0 and json_end > json_start:
        json_content = text[json_start:json_end]
        results = json.loads(json_content)
        return results.get("results", [])
    else:
        logger.warning("No JSON object found in the response")
        return []
