#!/usr/bin/env python
"""
Debug script for testing the ImprovedScriptWritingAgent.
This script tests the agent's ability to generate content for each section of a plan,
building upon the context of previously generated sections.
"""

import os
import json
import logging
from pprint import pprint

from dotenv import load_dotenv
from openai import OpenAI

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("script_writing_debug.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Import the improved agent
from web_app.backend.agents.improved_script_writing_agent import ImprovedScriptWritingAgent


def main():
    """Run the debug script with sample data."""
    # Load environment variables and initialize OpenAI client
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    # Sample topic and additional context
    topic = "The impact of AI on fraud detection"
    additional_context = """
    Financial institutions are increasingly facing sophisticated fraud attempts that 
    traditional systems struggle to detect. AI solutions offer a promising alternative,
    but their implementation requires careful consideration of technical, operational,
    and regulatory factors.
    """

    # Sample search results/references
    references = [
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
            "summary": "Sarah Breeden, Deputy Governor of the Bank of England, discusses the financial sector's increasing use of AI and the potential risks it poses. The BoE may include AI in its annual stress tests and has established an 'AI consortium' with private sector experts to study these risks further, emphasizing the need for managers to understand and manage AI models effectively.",
        },
    ]

    # Sample plan (provided by the user)
    plan = {
        "title": "Revolutionizing Fraud Detection with AI: Protecting Financial Services in the Digital Age",
        "target_audience": "Finance professionals, security specialists, and technology decision-makers in financial institutions",
        "duration": "12-15",
        "sections": [
            {
                "name": "Introduction & Context",
                "key_message": "Understand the urgent need to transition from outdated fraud detection systems to advanced AI-driven solutions.",
                "points": [
                    "Overview of the rising threat of online fraud and its impact on financial institutions.",
                    "Brief explanation of traditional fraud detection methods and why they are failing.",
                    "Introduction to AI's role in transforming fraud prevention.",
                ],
            },
            {
                "name": "Why Traditional Fraud Detection Systems Are Failing",
                "key_message": "Legacy fraud prevention systems are not equipped to tackle the sophisticated and evolving methods used by cybercriminals.",
                "points": [
                    "Reliance on rigid rules and manual checks that cannot adapt to new scam tactics.",
                    "High error rates and false positives that lead to missed fraud detection and customer dissatisfaction.",
                    "Discussion of modern cybercriminal techniques like identity spoofing, account takeovers, social engineering, and push-payment scams.",
                ],
            },
            {
                "name": "The Evolution: How AI Transforms Fraud Detection",
                "key_message": "AI introduces a multi-layered, adaptive approach that significantly improves fraud detection accuracy and operational efficiency.",
                "points": [
                    "Detailed breakdown of AI's three key levels: Identity Verification, Authentication, and Fraud Detection.",
                    "How AI processes diverse data sources, cross-references databases, and flags suspicious behaviors in real time.",
                    "Introduction to Graph Neural Networks (GNNs) and their ability to map global connections between accounts, devices, and actions.",
                ],
            },
            {
                "name": "Real-World Applications & Case Studies",
                "key_message": "Industry leaders are validating and benefiting from AI-driven fraud detection, underscoring the effectiveness of modern techniques in combating fraud.",
                "points": [
                    "Case Study: Banks leveraging cloud platforms (e.g., AWS and NVIDIA) using Amazon Neptune ML with GNNs to achieve higher prediction accuracy and cost efficiency.",
                    "Example: Visa's proactive approach in dismantling online scams, emphasizing their investment in AI and automated threat intelligence.",
                    "Analysis of the UK's new fraud rules that shift prevention responsibilities to banks and drive the integration of AI in fraud detection.",
                ],
            },
            {
                "name": "Future Trends & Considerations",
                "key_message": "While AI is revolutionizing fraud detection, continuous oversight, and evolving regulatory frameworks are essential to manage emerging risks.",
                "points": [
                    "Discussion on emerging risks associated with AI in financial services, including potential market manipulation.",
                    "Insights from the Bank of England about including AI in stress tests and the formation of an AI consortium.",
                    "Importance of balancing technological innovation with robust risk and model management frameworks.",
                ],
            },
            {
                "name": "Conclusion & Call to Action",
                "key_message": "Embracing AI is not just an option but a necessity for safeguarding financial services against increasingly sophisticated fraud.",
                "points": [
                    "Recap of the major points: limitations of traditional methods, the transformative power of AI, and the industry's move towards advanced analytics.",
                    "Final thoughts on the need for financial institutions to embrace AI to stay competitive and protect their clientele.",
                    "Encouragement for viewers to deepen their understanding, explore case studies, and consider AI solutions in their operations.",
                ],
            },
        ],
    }

    # Create an instance of ImprovedScriptWritingAgent
    writing_agent = ImprovedScriptWritingAgent(client=client)

    # Initialize an empty array to store the generated script sections
    generated_sections = []

    print("\n" + "=" * 80)
    print(f"TESTING SECTION-BY-SECTION GENERATION FOR TOPIC: {topic}")
    print("=" * 80 + "\n")

    # Generate script for each section in sequence, using previously generated content as context
    for i, section in enumerate(plan["sections"]):
        print(f"\nGenerating script for SECTION {i + 1}: {section['name']}")
        print("-" * 80)

        # Create a section-specific plan
        section_plan = {
            "title": plan["title"],
            "target_audience": plan["target_audience"],
            "duration": plan["duration"],
            "sections": [section],
        }

        # Prepare additional context that includes previously generated sections
        cumulative_context = additional_context
        if generated_sections:
            cumulative_context += "\n\nPreviously generated sections:\n"
            for j, prev_section in enumerate(generated_sections):
                cumulative_context += f"\n--- SECTION {j + 1}: {plan['sections'][j]['name']} ---\n"
                cumulative_context += prev_section

        # Generate the script for this section
        logger.info(f"Generating section {i + 1}/{len(plan['sections'])}: {section['name']}")
        logger.info(f"Section key message: {section['key_message']}")

        try:
            # Use the improved agent with section_only=True
            section_script = writing_agent.run(
                topic=topic,
                plan=section_plan,
                references=references,
                section_only=True,
                additional_context=cumulative_context,  # Pass the growing context
            )

            # Store the generated section
            generated_sections.append(section_script)

            # Log the result
            logger.info(
                f"Successfully generated content for section {i + 1}, length: {len(section_script)} chars"
            )

            # Print a preview
            print(f"\nSection Key Message: {section['key_message']}")
            print("\nGENERATED CONTENT PREVIEW:")
            print("-" * 40)
            preview = section_script[:500] + "..." if len(section_script) > 500 else section_script
            print(preview)
            print("-" * 40)

            # Save to a file for inspection
            section_filename = f"section_{i + 1}_{section['name'].replace(' ', '_')}.txt"
            with open(section_filename, "w") as f:
                f.write(section_script)
            print(f"\nFull content saved to {section_filename}")

        except Exception as e:
            logger.error(f"Error generating section {i + 1}: {str(e)}", exc_info=True)
            print(f"\nERROR generating section {i + 1}: {str(e)}")

    # Combine all sections into a complete script
    print("\n" + "=" * 80)
    print("COMBINING ALL SECTIONS INTO COMPLETE SCRIPT")
    print("=" * 80 + "\n")

    try:
        # Generate a complete script with all sections (for comparison)
        complete_script = writing_agent.run(
            topic=topic,
            plan=plan,
            references=references,
            section_only=False,
            additional_context=additional_context,
        )

        # Log and save the result
        logger.info(f"Successfully generated complete script, length: {len(complete_script)} chars")

        with open("complete_script.txt", "w") as f:
            f.write(complete_script)

        print(f"Complete script saved to complete_script.txt")

        # Also combine the individually generated sections
        assembled_script = ""
        for i, section in enumerate(plan["sections"]):
            assembled_script += f"\n\n{'#' * 3} {section['name']} {'#' * 3}\n\n"
            assembled_script += generated_sections[i]

        with open("assembled_script.txt", "w") as f:
            f.write(assembled_script)

        print(f"Assembled script saved to assembled_script.txt")

        # Compare statistics
        complete_word_count = len(complete_script.split())
        assembled_word_count = len(assembled_script.split())

        print("\nCOMPARISON STATISTICS:")
        print(f"Complete script word count: {complete_word_count}")
        print(f"Assembled script word count: {assembled_word_count}")
        print(f"Difference: {abs(complete_word_count - assembled_word_count)} words")

    except Exception as e:
        logger.error(f"Error generating complete script: {str(e)}", exc_info=True)
        print(f"\nERROR generating complete script: {str(e)}")

    print("\nDebug script completed!")


if __name__ == "__main__":
    main()
