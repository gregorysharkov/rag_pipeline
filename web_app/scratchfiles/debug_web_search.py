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

    🔥 Banks are turning to cloud platforms and advanced computing systems. For example, AWS and NVIDIA’s collaboration uses Amazon Neptune ML with GNNs to map complex relationships, boosting prediction accuracy by 50%. Tests show banks can train models 14x faster and cut costs 8x.

    As online fraud grows more sophisticated, outdated systems can’t keep up. Financial institutions that adopt AI will protect clients, safeguard their reputation, and gain a competitive edge.
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

    Format each result as follows:

    ## Result 1
    Title: [Title of the webpage]
    URL: [URL of the webpage]
    Summary: [Brief summary of the content]

    ## Result 2
    ...and so on

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
    # print("Raw response:")
    # print(generated_response)

    # Extract structured data from the text response
    results = extract_results_from_text(generated_response)

    # Print the extracted results
    # print("\nExtracted results:")
    # for i, result in enumerate(results, 1):
    #     print(f"\nResult {i}:")
    #     print(f"Title: {result.get('title')}")
    #     print(f"URL: {result.get('url')}")
    #     print(f"Summary: {result.get('summary')}")

    # Convert to JSON for further processing if needed
    results_json = json.dumps(results, indent=2)
    print(f"\n{'*' * 100}\nJSON format:")
    print(results_json)


def extract_results_from_text(text):
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
            r"\*?\*?Title:?\*?\*?\s*(?:\*?\*?)?(.*?)(?:\*?\*?)?\s*(?:\n|$)", section, re.IGNORECASE
        )
        if not title_match:
            # Try to find quoted title
            title_match = re.search(r'\*?\*?"([^"]+)"', section)

        if title_match:
            result["title"] = title_match.group(1).strip().strip('"')

        # Extract URL - handle both "URL:" and "**URL:**" formats
        url_match = re.search(
            r"\*?\*?URL:?\*?\*?\s*(?:\*?\*?)?(.*?)(?:\*?\*?)?\s*(?:\n|$)", section, re.IGNORECASE
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
            for key, item_value in result.items():
                if isinstance(item_value, str):
                    result[key] = item_value.replace("**", "").strip()

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
            summary_match = re.search(re.escape(url) + r".*?([^\n]+\n[^\n]+)", context, re.DOTALL)
            summary = summary_match.group(1).strip() if summary_match else "No summary available"

            results.append({"title": title, "url": url, "summary": summary})

    return results


if __name__ == "__main__":
    main()
