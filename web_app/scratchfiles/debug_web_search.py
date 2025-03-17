import json
import os
import re
from datetime import datetime

from dotenv import load_dotenv
from openai import OpenAI


def main():
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    # web_search_agent = WebSearchAgent(client)

    topic = "The impact of ai on fraud detection"
    additional_context = """
    🎯 Why Traditional Systems Are Failing
    🔹 Most legacy fraud prevention systems rely on rigid rules and manual checks. These methods struggle to adapt to new scams and often produce false results, with high error rates.
    🔹 Cybercriminals now use sophisticated tactics: identity spoofing, account takeovers, social engineering, and push-payment scams (where victims willingly transfer money to fraudsters).

    Banks and payment companies are now aggressively adopting AI solutions. AI operates at three key levels:
    1️⃣ Identity Verification: Analyzes data, cross-references databases, and flags suspicious users.
    2️⃣ Authentication: Detects behavioral patterns (typing speed, response time).
    3️⃣ Fraud Detection: Evaluates transactions, identifies anomalies, and blocks suspicious activity in real time.

    Graph Neural Networks (GNNs) are revolutionizing fraud prevention. Instead of analyzing single transactions, GNNs map global connections between accounts, devices, and actions.

    🔥 Banks are turning to cloud platforms and advanced computing systems. For example, AWS and NVIDIA's collaboration uses Amazon Neptune ML with GNNs to map complex relationships, boosting prediction accuracy by 50%. Tests show banks can train models 14x faster and cut costs 8x.

    As online fraud grows more sophisticated, outdated systems can't keep up. Financial institutions that adopt AI will protect clients, safeguard their reputation, and gain a competitive edge.
    """

    current_date = datetime.now().strftime(r"%Y-%m-%d")
    prompt = f"""
    IMPORTANT: YOUR ENTIRE RESPONSE MUST BE VALID JSON WITH NO OTHER TEXT.

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
    YOUR ENTIRE RESPONSE SHOULD BE PARSEABLE AS JSON.
    """

    # The gpt-4o-search-preview model has built-in web search capabilities
    # but doesn't support response_format with web_search
    response = client.chat.completions.create(
        model="gpt-4o-search-preview",
        messages=[
            {
                "role": "system",
                "content": prompt,
            },
            {
                "role": "user",
                "content": f"Search the web for information about: {topic}\n\nAdditional context: {additional_context}",
            },
        ],
    )

    generated_response = response.choices[0].message.content

    # Extract structured data from the text response
    results = extract_results_from_text(generated_response)

    # Convert to JSON for further processing if needed
    results_json = json.dumps(results, indent=2)
    print(f"\n{'*' * 100}\nJSON format:")
    print(results_json)


def extract_results_from_text(text):
    """Extract structured results from the text response."""
    try:
        print(f"text: {text}")
        # Try to find JSON content in the response
        json_start = text.find("{")
        json_end = text.rfind("}") + 1

        if json_start >= 0 and json_end > json_start:
            json_content = text[json_start:json_end]
            # Parse the JSON content
            results = json.loads(json_content)
            return results
        else:
            print("No JSON object found in the response")
            return {"results": []}
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        print(f"Response text: {text}")
        return {"results": []}


if __name__ == "__main__":
    main()
