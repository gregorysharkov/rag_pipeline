#!/usr/bin/env python3
"""
Test script to demonstrate individual file creation for news articles.
This creates sample articles to show the new file structure.
"""

import os
from datetime import datetime
from fetch_full_news import FullNewsProcessor


def create_sample_articles():
    """Create sample articles for testing the individual file structure."""

    sample_articles = [
        {
            "title": "Apple Announces Revolutionary iPhone 16 with AI Features",
            "source": {"name": "TechCrunch"},
            "author": "John Doe",
            "publishedAt": "2024-09-14T10:00:00Z",
            "url": "https://example.com/apple-iphone-16",
            "description": "Apple unveils the iPhone 16 with groundbreaking AI capabilities.",
            "content": "Apple today announced the iPhone 16, featuring advanced AI...",
            "extracted_content": """Apple today announced the iPhone 16, featuring advanced AI capabilities that will revolutionize how users interact with their devices. The new phone includes an enhanced Neural Engine capable of processing complex AI tasks locally on the device.

Key features include:
- Advanced AI-powered camera system with real-time scene recognition
- Improved Siri with contextual understanding
- Battery life optimized through AI-driven power management
- New AI writing assistant integrated system-wide

The iPhone 16 will be available in four models: iPhone 16, iPhone 16 Plus, iPhone 16 Pro, and iPhone 16 Pro Max. Pricing starts at $799 for the base model.

"This represents the biggest leap forward in iPhone technology since the original iPhone," said Tim Cook, Apple's CEO. "The integration of AI throughout the system creates an entirely new user experience."

Pre-orders begin this Friday, with general availability starting September 20th.""",
            "keywords": "Apple, iPhone 16, AI, artificial intelligence, smartphone, technology",
            "extraction_success": True,
        },
        {
            "title": "Microsoft Azure Sees 35% Growth in Q3 2024",
            "source": {"name": "Reuters"},
            "author": "Jane Smith",
            "publishedAt": "2024-09-13T15:30:00Z",
            "url": "https://example.com/microsoft-azure-growth",
            "description": "Microsoft reports strong Azure growth driven by AI services.",
            "content": "Microsoft Azure revenue grew 35% year-over-year...",
            "extracted_content": """Microsoft Azure revenue grew 35% year-over-year in the third quarter of 2024, driven primarily by increased adoption of AI-powered services and cloud infrastructure.

The growth was fueled by:
- Enterprise migration to cloud services accelerating post-pandemic
- Strong demand for AI and machine learning services
- Increased adoption of Microsoft 365 cloud productivity suite
- Growing market share in the competitive cloud computing space

"We're seeing unprecedented demand for our AI services," said Satya Nadella, Microsoft's CEO. "Organizations are recognizing the transformative potential of AI integrated with cloud infrastructure."

Azure's AI services, including Azure OpenAI Service, saw particularly strong growth with over 200% increase in usage compared to the previous quarter.

Microsoft's total cloud revenue reached $28.5 billion for the quarter, representing 45% of total company revenue.""",
            "keywords": "Microsoft, Azure, cloud computing, AI services, Q3 2024, growth",
            "extraction_success": True,
        },
    ]

    return sample_articles


def main():
    """Test the individual file creation functionality."""
    print("🧪 Testing Individual File Creation")
    print("=" * 50)

    # Create a test instance (no API key needed for this test)
    processor = FullNewsProcessor("test_key", output_dir="notebooks/documents/")

    # Test with sample data
    companies_and_articles = [
        ("Apple", create_sample_articles()[:1]),  # First article for Apple
        ("Microsoft", create_sample_articles()[1:]),  # Second article for Microsoft
    ]

    for company, articles in companies_and_articles:
        print(f"\n📰 Testing {company} with {len(articles)} article(s)")
        processor.save_individual_articles(company, articles)

    print("\n✅ Test completed! Check the notebooks/documents/ directory for results.")
    print("\nFile structure created:")

    # Show the created structure
    base_dir = "notebooks/documents"
    if os.path.exists(base_dir):
        for root, dirs, files in os.walk(base_dir):
            level = root.replace(base_dir, "").count(os.sep)
            indent = " " * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = " " * 2 * (level + 1)
            for file in files:
                if file.endswith(".txt"):
                    print(f"{subindent}{file}")


if __name__ == "__main__":
    main()
