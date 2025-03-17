import os

from dotenv import load_dotenv
from openai import OpenAI

# from backend.agents.planning_agent import PlanningAgent


def main():
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

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
    search_results = [
        {
            "title": "Supercharging Fraud Detection in Financial Services with Graph Neural Networks",
            "url": "https://developer.nvidia.com/blog/supercharging-fraud-detection-in-financial-services-with-graph-neural-networks/",
            "summary": "This article discusses the integration of Graph Neural Networks (GNNs) in fraud detection, emphasizing their ability to analyze complex relationships between accounts, devices, and transactions. By mapping these connections, GNNs enhance the detection of fraudulent activities, offering improved accuracy and scalability over traditional methods.",
        },
        {
            "title": "Visa sets up new team to take down all scammers",
            "url": "https://www.axios.com/2025/03/11/visa-scam-disruption-practice-fraud",
            "summary": "Visa has established a dedicated team to proactively detect and dismantle online scam operations. This initiative focuses on expanding intelligence-gathering, accelerating scam takedowns, and investing in AI and automation to enhance detection capabilities, underscoring Visa's commitment to safeguarding its customers against fraud.",
        },
        {
            "title": "Are you protected by the UK's new fraud rules?",
            "url": "https://www.ft.com/content/cc1bf03a-7a7b-4977-b74a-c97f54ee8601",
            "summary": "The UK's new fraud regulations, effective from October 7, mandate faster reimbursements for victims of push payment fraud and shift the burden of fraud prevention to banks. This compels financial institutions to invest significantly in detection and prevention technologies, including AI, to meet regulatory requirements and protect consumers.",
        },
        {
            "title": "Optimizing Fraud Detection in Financial Services with Graph Neural Networks and NVIDIA GPUs",
            "url": "https://developer.nvidia.com/blog/optimizing-fraud-detection-in-financial-services-with-graph-neural-networks-and-nvidia-gpus/",
            "summary": "This technical blog explores the application of GNNs accelerated by NVIDIA GPUs in fraud detection. It highlights the challenges of traditional methods and demonstrates how GNNs can effectively model complex fraud patterns, offering enhanced detection capabilities and scalability for financial institutions.",
        },
        {
            "title": "Banks' use of AI could be included in stress tests, says Bank of England deputy governor",
            "url": "https://www.ft.com/content/d4d212a8-c63a-4b00-9f4c-e06ed59f9279",
            "summary": "Sarah Breeden, Deputy Governor of the Bank of England, discusses the financial sector's increasing use of AI and the potential risks it poses. The BoE may include AI in its annual stress tests and has established an \u201cAI consortium\u201d with private sector experts to study these risks further, emphasizing the need for managers to understand and manage AI models effectively.",
        },
    ]

    references_text = "\n\n".join(
        [
            f"Reference {i + 1}:\nTitle: {ref['title']}\nURL: {ref['url']}\nSummary: {ref['summary']}"
            for i, ref in enumerate(search_results)
        ]
    )

    # TODO: add target audience to the prompt
    # TODO: add key takeaways to the prompt
    prompt = f"""
    You are a video script planning agent. Your task is to create a detailed plan for a YouTube video about: {topic}

    User provided additional context:
    {additional_context}

    Here are the references to incorporate, if possible:
    {references_text}

    Create a comprehensive plan that incorporates the topic, the user provided additional context, and the references, that includes:
    1. Video title
    2. Target audience
    3. Estimated duration (in minutes)
    4. Key sections

    The result should be only a JSON object. Please do not include any other text in your response.
    format of the json object:
    {{
        "title": "string",
        "target_audience": "string",
        "duration": "number",
        "sections": [
            {{
                "name": "string",
                "points": ["string"],
                "key_message": "string"
            }}
        ]
    }}
    """

    response = client.chat.completions.create(
        model="o1",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )

    print(response.choices[0].message.content)


if __name__ == "__main__":
    main()
