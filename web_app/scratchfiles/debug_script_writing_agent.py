import os

from dotenv import load_dotenv
from openai import OpenAI


def main():
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

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

    plan_result = {
        "title": "How AI is Transforming Fraud Detection: From Legacy Pitfalls to Next-Gen Protection",
        "target_audience": "Banking executives, financial technology professionals, risk management specialists, startup founders in finance, and anyone interested in understanding how modern AI systems can protect against fraud in the financial sector",
        "duration": 9,
        "sections": [
            {
                "name": "Introduction: The Rise of AI-Based Fraud Detection",
                "points": [
                    "Hook: Examples of high-profile fraud incidents and how they stress-test traditional security methods",
                    "Brief overview of legacy fraud prevention challenges: slow adaptation, high false positives, manual checks",
                    "Tease the role AI is playing to solve these issues, referencing how cloud platforms and advanced systems are enabling faster, more accurate detection",
                ],
                "key_message": "AI is rapidly emerging as the new cornerstone of fraud detection, bridging major gaps left by traditional systems and preparing financial institutions for evolving threats.",
            },
            {
                "name": "Why Traditional Systems Are Failing",
                "points": [
                    "Rigid rule-based systems can't adapt quickly to new scams (push-payment scams, identity theft, etc.)",
                    "High error rates and resource-heavy manual investigations",
                    "Accelerated innovation by fraudsters employing identity spoofing, social engineering, and sophisticated tactics",
                ],
                "key_message": "Manual and rule-based approaches are too static and costly, unable to handle the rapidly changing landscape of modern financial fraud.",
            },
            {
                "name": "The Three Key Levels of AI Fraud Prevention",
                "points": [
                    "Identity Verification: Using data analysis to spot anomalies in user details and referencing multiple databases",
                    "Authentication: Analyzing behavioral patterns such as typing speed, device fingerprinting, or reaction times to detect suspicious logins",
                    "Fraud Detection: Real-time transaction analysis to flag and terminate fraudulent activities before losses escalate",
                ],
                "key_message": "Robust AI solutions operate on multiple layers—verifying identity, authenticating behavior, and proactively detecting fraudulent transactions in real time.",
            },
            {
                "name": "Graph Neural Networks (GNNs): A Game-Changer",
                "points": [
                    "Overview of GNNs and how they map complex relationships (Reference 1: NVIDIA blog on GNNs)",
                    "Collaboration between AWS and NVIDIA, using Amazon Neptune ML to boost prediction accuracy by 50% and train models 14x faster (Reference 1)",
                    "Why mapping global connections between accounts, devices, and transactions uncovers hidden fraud rings more effectively than single-transaction analysis",
                ],
                "key_message": "GNNs expand fraud detection beyond isolated events, enabling holistic pattern recognition across vast networks of financial interactions.",
            },
            {
                "name": "Real-World Cases: Industry-Leading Efforts",
                "points": [
                    "Visa’s new team dedicated to proactively cracking down on online scams, preventing $350 million in attempted fraud in 2024 (Reference 2)",
                    "How these initiatives underscore the industry’s urgency in adopting AI and automation solutions",
                ],
                "key_message": "Major industry players like Visa are investing heavily in AI-driven strategies, underscoring a strong commitment to proactive fraud detection.",
            },
            {
                "name": "Regulatory Shifts and Their Impact",
                "points": [
                    "UK’s new fraud regulations targeting push-payment scams and requiring expedited reimbursement (Reference 3)",
                    "Heightened pressure on banks to invest in AI for prevention and detection to meet regulatory standards",
                ],
                "key_message": "Tougher regulations are forcing financial institutions to scale AI readiness, benefiting consumers through quicker reimbursements and stronger fraud safeguards.",
            },
            {
                "name": "Emerging Threats: AI-Driven Disinformation & Stress Tests",
                "points": [
                    "AI-generated content fueling potential bank runs via viral misinformation (Reference 4)",
                    "Bank of England’s discussion on including AI in stress tests due to generative AI risks like market manipulation (Reference 5)",
                ],
                "key_message": "AI can be a double-edged sword—while it fortifies fraud detection, it also amplifies new threat vectors like disinformation, requiring vigilance and regulatory oversight.",
            },
            {
                "name": "Conclusion: Gaining a Competitive Edge",
                "points": [
                    "Summarize key benefits of AI-based fraud prevention: reduced costs, enhanced reputation, real-time detection",
                    "Emphasize the competitive advantage of implementing robust, adaptive systems",
                    "Final call to action encouraging financial institutions and fintech innovators to align with AI-driven fraud prevention for sustained trust and growth",
                ],
                "key_message": "By investing in AI for fraud detection, financial institutions protect clients, reinforce trust, and secure a leading market position—staying ahead in an ever-evolving threat environment.",
            },
        ],
    }

    for section in plan_result["sections"]:
        prompt = f"""
        You are a script writing agent that is writing a part of ascript for a video about the topic: {topic}.

        You need to write a script for section {section["name"]}.
        The key message is: {section["key_message"]}
        The points are: {section["points"]}

        focus on the text of the script and instructions to the Narrator, ignoring the vizual and audiocomponents of the script.
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        print("-" * 100)
        print(f"Section: {section['name']}")
        print(response.choices[0].message.content)


if __name__ == "__main__":
    main()
