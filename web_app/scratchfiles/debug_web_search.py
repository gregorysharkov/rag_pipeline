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

    # The gpt-4o-search-preview model has built-in web search capabilities
    print("Sending request to search API...")
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
    print("\nRaw response from API:")
    print("-" * 50)
    print(generated_response[:500] + "..." if len(generated_response) > 500 else generated_response)
    print("-" * 50)

    # Save the raw response to a file for inspection
    with open("raw_search_response.txt", "w") as f:
        f.write(generated_response)
    print("Full raw response saved to raw_search_response.txt")

    # Parse the response as JSON
    try:
        results = parse_json_response(generated_response)
        print(f"Successfully extracted {len(results)} results using JSON parser")

        # Convert to JSON for further processing
        results_json = json.dumps(results, indent=2)
        print(f"\n{'*' * 100}\nProcessed JSON format:")
        print(results_json)

        # Save the processed results to a file
        with open("processed_search_results.json", "w") as f:
            f.write(results_json)
        print("Processed results saved to processed_search_results.json")
    except Exception as e:
        print(f"JSON parsing failed: {str(e)}")
        print("No results could be extracted from the response")


def parse_json_response(text):
    """Extract JSON from the response text."""
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
        raise ValueError("Could not find valid JSON in the response")


if __name__ == "__main__":
    main()
