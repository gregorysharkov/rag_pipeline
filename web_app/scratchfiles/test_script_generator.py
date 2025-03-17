#!/usr/bin/env python
"""
Test script for the YouTube shorts script generator.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))
    print(f"Added {project_root} to Python path")

# Import the script generator
from src.rag_pipeline.pipelines.generate_script.nodes import generate_youtube_short_script


def main():
    """Test the script generator."""
    print("Testing the YouTube shorts script generator...")

    # Test topic
    topic = "Artificial Intelligence in 2024"

    print(f"\nGenerating script for topic: {topic}\n")

    # Generate the script
    script = generate_youtube_short_script(topic)

    # Print the script
    print("=" * 80)
    print(script)
    print("=" * 80)

    print("\nScript generation completed successfully!")


if __name__ == "__main__":
    main()
