COMMON_SEARCH_INSTRUCTIONS = """
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
If additional context contains questions, make sure that the summary contains answers to the questions.
{{
    "results": [
        {{
            "title": "The Actual Title of the Webpage",
            "url": "https://real-website.com/actual-page",
            "summary": "Actual summary of the content from the page, facts that are relevant to the topic and can be used to create content on the topic."
        }},
        ...
    ]
}}

DO NOT include any explanations, introductions, or notes outside the JSON structure.
DO NOT use markdown formatting around the JSON.
DO NOT write "```json" or any other text before or after the JSON.
YOUR ENTIRE RESPONSE SHOULD BE PARSEABLE AS JSON.
"""
