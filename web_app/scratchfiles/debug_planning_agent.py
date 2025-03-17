import os
from dotenv import load_dotenv
from openai import OpenAI


def main():
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    topic = "The impact of ai on fraud detection"

    search_results = [
        {
            "title": "Supercharging Fraud Detection in Financial Services with Graph Neural Networks",
            "url": "https://developer.nvidia.com/blog/supercharging-fraud-detection-in-financial-services-with-graph-neural-networks/",
            "summary": "This article discusses the limitations of traditional fraud detection methods and introduces Graph Neural Networks (GNNs) as a solution. GNNs analyze complex relationships between accounts, devices, and transactions, enhancing the detection of sophisticated fraud patterns. The piece also highlights a collaboration between AWS and NVIDIA, utilizing Amazon Neptune ML with GNNs to improve prediction accuracy by 50%, train models 14 times faster, and reduce costs by 8 times.",
            "id": "1",
        },
        {
            "title": "Optimizing Fraud Detection in Financial Services with Graph Neural Networks and NVIDIA GPUs",
            "url": "https://developer.nvidia.com/blog/optimizing-fraud-detection-in-financial-services-with-graph-neural-networks-and-nvidia-gpus/",
            "summary": "This blog post explores the challenges of fraud detection in financial services and presents Graph Neural Networks (GNNs) as an effective tool. GNNs consider the connections between transactions, accounts, and devices, enabling the identification of complex fraud patterns. The article details an end-to-end AI workflow using GNNs, optimized with NVIDIA GPUs, to enhance fraud detection capabilities.",
            "id": "2",
        },
        {
            "title": "Exclusive: Visa sets up new team to take down all scammers",
            "url": "https://www.axios.com/2025/03/11/visa-scam-disruption-practice-fraud",
            "summary": "Visa has established a new initiative aimed at detecting and dismantling online scammers to protect customers, addressing the growing scam ecosystem. This effort arises as consumers lost over $1 trillion to scams globally last year, and law enforcement struggles to manage the sheer volume of online scams. Modeled after threat intelligence units in cybersecurity, Visa's team proactively studies and disrupts scam operations, having already thwarted over $350 million in attempted fraud in 2024. The team focuses on expanding intelligence-gathering, accelerating scam takedowns, and investing in AI and automation to enhance detection capabilities. This initiative underscores Visa's commitment to safeguarding its customers and platforms against fraud.",
            "id": "3",
        },
        {
            "title": "Are you protected by the UK's new fraud rules?",
            "url": "https://www.ft.com/content/cc1bf03a-7a7b-4977-b74a-c97f54ee8601",
            "summary": "The UK's new fraud rules, effective from October 7, promise faster reimbursements for victims of push payment fraud, aiming to return money within five working days. This initiative shifts the burden of fraud prevention to banks, compelling them to invest significantly in detection and prevention. Last year, nearly 3 million Britons lost over £1.1 billion to fraud. While the new regulations cap automatic reimbursements at £85,000, cases above this will be dealt with individually, potentially causing delays in high-value cases. Banks are now required to share responsibility for fraudulent transactions, urging all financial institutions to heighten their fraud prevention measures. There are concerns about new risks and \"moral hazard\" if customers become complacent about security. Banks will also begin using AI technology to better detect and prevent fraud. A year-long review of the system's effectiveness is planned, as the industry adjusts to these significant changes.",
            "id": "4",
        },
        {
            "title": "AI-generated content raises risks of more bank runs, UK study shows",
            "url": "https://www.reuters.com/technology/artificial-intelligence/ai-generated-content-raises-risks-more-bank-runs-uk-study-shows-2025-02-14/",
            "summary": "A UK study has highlighted the increased risk of bank runs due to AI-generated disinformation spread on social media. The study, conducted by Say No to Disinfo and Fenimore Harper, warns that AI can create fake news and memes about bank security, leading to significant withdrawals. This follows concerns raised after the 2023 Silicon Valley Bank collapse, where $42 billion was withdrawn in 24 hours, exacerbated by social media. The G20’s Financial Stability Board previously noted that generative AI could cause financial crises. The UK study showed that a significant portion of bank customers would consider moving their money after viewing AI-generated fake content. Banks are urged to enhance media and social media monitoring to identify and mitigate the impact of disinformation. The report estimated that £10 spent on social media ads could lead to the movement of up to £1 million in deposits. Financial institutions and regulators are increasingly attentive to the risks, and the study calls for greater involvement from social media platforms in addressing these threats.",
            "id": "5",
        },
    ]
    references_text = "\n".join(
        [f"{result['title']}\n{result['url']}\n{result['summary']}" for result in search_results]
    )

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

    prompt = f"""
    You are a video script planning agent. Your task is to create a detailed plan for a YouTube video about: {topic}

    Here are the references to incorporate:
    {references_text}

    Create a comprehensive plan that includes:
    1. Video title
    2. Target audience
    3. Estimated duration (in minutes)
    4. Key sections
    Each section should have a name, a list of key points and the key message


    Format your response as a JSON object with keys: "title", "target_audience", "duration", "sections" (array of objects with "name", "points", "key message") (array)
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )

    print(response.choices[0].message.content)


if __name__ == "__main__":
    main()
