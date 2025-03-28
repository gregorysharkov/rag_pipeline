import logging
import os
import sys
from pathlib import Path

from openai import OpenAI

# Add the parent directory to the Python path
# This allows importing the web_app module


def main():
    parent_dir = str(Path(__file__).parent.parent.parent)
    sys.path.append(parent_dir)

    from dotenv import load_dotenv

    # Set up logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler("script_writing_debug.log"), logging.StreamHandler()],
    )
    logger = logging.getLogger(__name__)
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    script = """
    **[Introduction: More Than Meets the Eye]**
    You've probably seen an AI Agent in action and thought, "Oh, it's just chatting with me. How complicated can it be?" But there's a whole world tucked beneath that conversation box. Under the surface, you have CPU and GPU providers supplying serious computing power—so these models can learn, reason, and respond in real time. Then there's the infrastructure layer that handles deployment at scale, along with databases juggling everything from structured records to unstructured text. Foundational models form the core intelligence of an AI Agent, but even they don't do it alone. Smart model routing chooses which model is best for a particular query, while agent orchestration keeps multiple agents working together smoothly on complex tasks. Observability tools track how the AI is behaving, memory layers allow the agent to remember what's been said or learned, and specialized tools let it retrieve real-world updates or tap into external services. Finally, all of this is wrapped in a front-end interface that makes the AI Agent feel as simple as any ordinary chatbot—even though it's really powered by an entire stack of hardware, software, and processes working in sync behind the scenes.

    **[Foundational Layers: Computing and Deployment]**
    When AI agents run complex models, they need serious computing firepower behind the scenes. That's where CPU and GPU providers come in, delivering the performance and scalability required for training massive models and handling real-time inference workloads. According to a developer's perspective (Reference 2), tapping into these resources—whether through cloud providers or on-prem data centers—ensures your AI agents can operate smoothly at any scale.
    Then there's the infrastructure layer, which takes this raw power and wraps it in a containerized environment. By packaging agents and their dependencies in containers, teams can rapidly deploy updates, isolate workloads, and optimize connectivity across different systems. This approach also makes it easier to roll out new features, scale on demand, and maintain reliability, all of which are critical for agent applications that must respond quickly to user needs.
    Behind the scenes, databases play an equally important role. AI agents work with both structured data—like user profiles or logs—and unstructured data—such as text documents and images. According to insights on autonomous AI systems (Reference 3), a hybrid storage solution allows you to mix transactional, time-series, and vector databases for optimal performance. The result is fast retrieval of relevant information, plus the ability to handle the massive variety and volume of data today's AI agents rely on to make informed decisions. By combining these robust compute resources, flexible infrastructure, and intelligent data management strategies, you lay the groundwork for AI agents that can truly power real-world applications.

    **[The Brains: Foundational & Specialized Models]**
    At the heart of an AI agent's intelligence are its models—both the large, foundational models and the more specialized varieties. Think of the foundational models like broad problem-solvers that can handle everything from text generation to reasoning, while smaller or retrieval-augmented models give you more focused capabilities. This balance matters because not every task demands the powerhouse of a massive language model. In many real-world scenarios, a compact model—enhanced with domain-specific data—can be more efficient and cost-effective.
    One of the biggest challenges is handling context. Models need to remember user interactions, adapt to new information, and incorporate feedback over time. That often involves layering memory components or leveraging external databases, so the AI can dynamically update its internal "knowledge base" rather than sticking to a frozen snapshot.
    Another consideration is whether to use open-source or commercial solutions. Open-source models give you more flexibility and control, which can be crucial for customizing or integrating deeply with existing systems. Commercial models, on the other hand, might offer more streamlined support, security features, or specialized optimizations out of the box. Ultimately, there's no one-size-fits-all choice—it comes down to balancing task requirements, budget, and the level of control you need to keep your AI agents both powerful and efficient.

    **[Model Routing & Orchestration]**
    When a user query comes in, model routing makes sure it gets matched to the most suitable AI model. It's not always about throwing the biggest, most complex model at every problem—sometimes a smaller or specialized model can handle the task more efficiently or cost-effectively. By considering factors like complexity, latency, and budget, routing helps you strike that balance between performance and resource usage. 
    Then there's orchestration, which steps in to coordinate all these moving parts. In many enterprise settings, you're dealing with multiple agents working hand in hand—one might handle language parsing, another might manage data retrieval, and yet another could specialize in recommendation tasks. Orchestration frameworks ensure these agents communicate seamlessly, automate repetitive steps, and structure decision flows so they can operate in parallel or in a specific sequence. 
    The power of orchestration really shows up when you tie it with the larger infrastructure surrounding AI agents—like tools that provide real-time data, databases that feed essential context, or operational workflows that keep everything running smoothly at scale. When routing and orchestration work together, you get a streamlined system that quickly identifies which model to use, delegates tasks across multiple agents, and monitors outcomes in real-time. That holistic approach helps AI agents stay both agile and efficient, even in the most demanding environments.

    **[Tools, Observability, and Memory]**
    When AI agents tap into external APIs, search engines, or specialized integrations, they suddenly gain the ability to reach beyond their own training data. That means better answers, faster responses, and more sophisticated skills—like pulling live information or automating entire workflows. But having these tools isn't enough on its own. We also need detailed observability to keep track of what's really going on under the hood. Think of it as a real-time dashboard that shows crucial metrics, behaviors, and even the exact text prompts guiding agent decisions. With that insight, developers can quickly spot issues, optimize performance, and continuously refine how agents interact with users. And then there's the memory layer, which ties everything together by letting agents remember past conversations and maintain context over time. This enables more natural, personalized responses and helps the agent learn from every single user interaction. By combining powerful tools, real-time observability, and robust memory, AI agents become not just knowledgeable, but adaptable and always improving.

    **[Front-end and User Experience]**
    A polished front-end is where all the behind-the-scenes complexity finally comes together in a way that feels effortless to users. According to the developer-focused insights shared in "Architecting AI Agents: A Developer's View," well-structured web or app frameworks go a long way in driving user engagement. When your UI matches user expectations—offering clean layouts, consistent design elements, and intuitive navigation—it becomes far easier for people to adopt and trust an AI solution.
    By making user input and responses clear and easy to follow, a good front-end emphasizes the human element. Building on the orchestration and data layers (highlighted in discussions of AI agent infrastructure), the UI essentially "translates" complex operations like context retrieval, model routing, and multi-agent collaboration into a simple, interactive dialogue on the user's screen. This seamless communication can have a major impact on how quickly and comfortably users embrace AI-driven functionality.
    Ultimately, when the front-end is designed with clarity in mind—from straightforward prompts to accessible help menus—it significantly boosts user satisfaction. People become more confident in exploring what AI agents can do when they don't have to wrestle with a confusing interface. And that confidence translates directly into broader adoption, especially in developer and business settings where time is scarce and attention is limited.

    **[Conclusion: The Future of AI Agent Infrastructure]**
    We've seen that powering AI Agents isn't just about training a single model—it's a collective effort across multiple layers working together in harmony. From the processors delivering raw computing power, to the infrastructure that handles containerization and connectivity, to the databases that store everything from transactional records to real-time and unstructured data—every layer must be both modular and scalable. And it doesn't stop there: model routing plays a strategic role in matching each query to the right AI model, while agent orchestration ensures that tasks are streamlined and, in many cases, fully automated. 
    As standardized protocols like the Model Context Protocol gain traction, we'll see even smoother integration of tools and services. This approach paves the way for more specialized databases—such as vector search systems for unstructured data—and more advanced orchestration frameworks that can juggle complex workflows in real time. The result? AI Agents that can operate autonomously, adapt quickly, and maintain a streamlined context for better decision-making. 
    It's clear that this layered, modular stack will continue evolving, driving us toward AI systems that are not only more powerful and efficient, but also increasingly autonomous. Whether you're a developer, a data scientist, or a product manager, understanding—and taking advantage of—this robust infrastructure will be crucial for shaping the future of AI Agent technologies.
    """

    edit_options = ["conversational", "humor"]
    additional_instructions = "Add examples where appropriate"

    promt = f"""
    You are an expert script editor. Your task is to edit the following script according to provided instructions.
    The scrip is separated in sections using the following pattern `**section_name**`, please edit each section separately.

    ORIGINAL SCRIPT:
    {script}

    EDITING REQUIREMENTS:
    {edit_options}

    ADDITIONAL INSTRUCTIONS:
    {additional_instructions}

    Add into with a rethorical question as an engaging hook in the beginning.
    Add a call to action at the end.
    """
    # print(promt)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": promt}],
        )
        print("*" * 100, "Response:")
        print(response.choices[0].message.content)
    except Exception as e:
        print(e)

if __name__ == "__main__":
    main()
