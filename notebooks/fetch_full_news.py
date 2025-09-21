#!/usr/bin/env python3
"""
Enhanced News Fetcher Script with Full Content Extraction

This script fetches news articles and extracts full content by scraping the article URLs.
Uses newspaper3k library for robust content extraction.

Requirements:
- NewsAPI key in .env file as NEWS_API_KEY
- Internet connection
- newsapi-python and newspaper3k libraries installed

Usage:
    python fetch_full_news.py
"""

import os
import time
from datetime import datetime
from typing import Any

import requests
from dotenv import load_dotenv
from newsapi import NewsApiClient
from newspaper import Article
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class FullNewsProcessor:
    """Enhanced news processor that extracts full article content."""

    def __init__(self, api_key: str, output_dir: str = "notebooks/documents/"):
        """
        Initialize the enhanced news processor.

        Args:
            api_key: NewsAPI key
            output_dir: Directory to save news files
        """
        self.newsapi = NewsApiClient(api_key=api_key)
        self.output_dir = output_dir
        self.ensure_output_directory()

        # Setup requests session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def ensure_output_directory(self):
        """Create output directory if it doesn't exist."""
        os.makedirs(self.output_dir, exist_ok=True)
        print(f"Output directory: {os.path.abspath(self.output_dir)}")

    def extract_full_content(self, url: str) -> dict[str, str]:
        """
        Extract full content from article URL using newspaper3k.

        Args:
            url: Article URL

        Returns:
            dictionary with extracted content
        """
        try:
            # Initialize Article object
            article = Article(url)

            # Download and parse
            article.download()
            article.parse()

            return {
                "full_text": article.text,
                "title": article.title,
                "authors": ", ".join(article.authors) if article.authors else "N/A",
                "publish_date": str(article.publish_date) if article.publish_date else "N/A",
                "summary": article.summary if hasattr(article, "summary") else "",
                "keywords": ", ".join(article.keywords) if article.keywords else "",
                "extraction_success": True,
            }

        except Exception as e:
            print(f"    ⚠️ Failed to extract content from {url}: {str(e)}")
            return {
                "full_text": "",
                "title": "",
                "authors": "",
                "publish_date": "",
                "summary": "",
                "keywords": "",
                "extraction_success": False,
                "error": str(e),
            }

    def fetch_company_news(self, company: str, num_articles: int = 5) -> list[dict[str, Any]]:
        """
        Fetch news articles for a specific company.

        Args:
            company: Company name to search for
            num_articles: Number of articles to fetch

        Returns:
            List of news articles
        """
        try:
            print(f"🔍 Fetching news for {company}...")

            # Fetch news using NewsAPI
            response = self.newsapi.get_everything(
                q=company, language="en", sort_by="relevancy", page_size=num_articles
            )

            if response["status"] == "ok":
                articles = response["articles"][:num_articles]
                print(f"  ✅ Found {len(articles)} articles for {company}")
                return articles
            else:
                print(
                    f"  ❌ Error fetching news for {company}: {response.get('message', 'Unknown error')}"
                )
                return []

        except Exception as e:
            print(f"  ❌ Exception while fetching news for {company}: {str(e)}")
            return []

    def enhance_articles_with_full_content(
        self, articles: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Enhance articles with full content extraction.

        Args:
            articles: List of articles from NewsAPI

        Returns:
            Enhanced articles with full content
        """
        enhanced_articles = []

        for i, article in enumerate(articles, 1):
            print(f"    📄 Extracting full content for article {i}/{len(articles)}...")

            # Extract full content
            url = article.get("url", "")
            if url:
                extracted = self.extract_full_content(url)

                # Combine original article data with extracted content
                enhanced_article = {
                    **article,  # Original NewsAPI data
                    "extracted_content": extracted["full_text"],
                    "extracted_title": extracted["title"],
                    "extracted_authors": extracted["authors"],
                    "extracted_date": extracted["publish_date"],
                    "extracted_summary": extracted["summary"],
                    "keywords": extracted["keywords"],
                    "extraction_success": extracted["extraction_success"],
                }

                if not extracted["extraction_success"]:
                    enhanced_article["extraction_error"] = extracted.get("error", "Unknown error")

                enhanced_articles.append(enhanced_article)

                # Add delay to be respectful to websites
                time.sleep(1)
            else:
                print(f"    ⚠️ No URL found for article {i}")
                enhanced_articles.append(article)

        return enhanced_articles

    def save_individual_articles(self, company: str, articles: list[dict[str, Any]]):
        """
        Save each news article as a separate file.

        Args:
            company: Company name
            articles: List of enhanced news articles
        """
        if not articles:
            print(f"  No articles to save for {company}")
            return

        # Create company-specific subdirectory
        safe_company_name = "".join(
            c for c in company if c.isalnum() or c in (" ", "-", "_")
        ).rstrip()
        company_dir = os.path.join(self.output_dir, safe_company_name.replace(" ", "_").lower())
        os.makedirs(company_dir, exist_ok=True)

        successful_extractions = 0
        saved_files = []

        try:
            # Save each article as a separate file
            for i, article in enumerate(articles, 1):
                # Create safe filename from article title
                title = article.get("title", f"Article_{i}")
                safe_title = "".join(
                    c for c in title if c.isalnum() or c in (" ", "-", "_")
                ).strip()
                safe_title = safe_title.replace(" ", "_")[:50]  # Limit length

                # Add timestamp to avoid duplicates
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{safe_title}_{timestamp}.txt"
                filepath = os.path.join(company_dir, filename)

                with open(filepath, "w", encoding="utf-8") as file:
                    # Write article header
                    file.write(f"COMPANY: {company.upper()}\n")
                    file.write(f"ARTICLE: {i}/{len(articles)}\n")
                    file.write(f"GENERATED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    file.write("=" * 80 + "\n\n")

                    # Article metadata
                    file.write(f"TITLE: {article.get('title', 'N/A')}\n")
                    file.write(f"SOURCE: {article.get('source', {}).get('name', 'N/A')}\n")
                    file.write(f"AUTHOR: {article.get('author', 'N/A')}\n")
                    file.write(f"PUBLISHED: {article.get('publishedAt', 'N/A')}\n")
                    file.write(f"URL: {article.get('url', 'N/A')}\n")
                    file.write(f"DESCRIPTION: {article.get('description', 'N/A')}\n")

                    # Extraction status
                    extraction_success = article.get("extraction_success", False)
                    file.write(
                        f"EXTRACTION_STATUS: {'SUCCESS' if extraction_success else 'FAILED'}\n"
                    )

                    if extraction_success:
                        successful_extractions += 1
                        if article.get("keywords"):
                            file.write(f"KEYWORDS: {article.get('keywords')}\n")

                    file.write("\n" + "-" * 80 + "\n")
                    file.write("CONTENT:\n")
                    file.write("-" * 80 + "\n\n")

                    # Article content
                    if extraction_success:
                        full_content = article.get("extracted_content", "")
                        if full_content:
                            file.write(full_content)
                        else:
                            file.write("No content extracted despite successful extraction status.")
                    else:
                        # Fallback to original truncated content
                        original_content = article.get("content", "No content available")
                        file.write(original_content)

                        if article.get("extraction_error"):
                            file.write(f"\n\n[EXTRACTION ERROR: {article.get('extraction_error')}]")

                saved_files.append(filepath)
                print(f"    💾 Saved: {os.path.basename(filepath)}")

            print(f"  ✅ Saved {len(articles)} individual articles to {company_dir}")
            print(
                f"  📊 Full content extracted for {successful_extractions}/{len(articles)} articles"
            )

            # Create index file for the company
            # self.create_company_index(company, company_dir, saved_files, articles)

        except Exception as e:
            print(f"  ❌ Error saving articles for {company}: {str(e)}")

    def create_company_index(
        self, company: str, company_dir: str, saved_files: list[str], articles: list[dict[str, Any]]
    ):
        """
        Create an index file listing all articles for a company.

        Args:
            company: Company name
            company_dir: Directory where articles are saved
            saved_files: List of saved file paths
            articles: List of articles with metadata
        """
        index_filename = f"_{company.lower()}_index.txt"
        index_filepath = os.path.join(company_dir, index_filename)

        try:
            with open(index_filepath, "w", encoding="utf-8") as file:
                file.write(f"NEWS ARTICLES INDEX FOR {company.upper()}\n")
                file.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                file.write(f"Total articles: {len(articles)}\n")
                file.write(f"Directory: {company_dir}\n")
                file.write("=" * 80 + "\n\n")

                for i, (filepath, article) in enumerate(zip(saved_files, articles), 1):
                    filename = os.path.basename(filepath)
                    title = article.get("title", "N/A")
                    source = article.get("source", {}).get("name", "N/A")
                    published = article.get("publishedAt", "N/A")
                    extraction_status = "✅" if article.get("extraction_success", False) else "❌"

                    file.write(f"{i:2d}. {filename}\n")
                    file.write(f"    Title: {title}\n")
                    file.write(f"    Source: {source}\n")
                    file.write(f"    Published: {published}\n")
                    file.write(f"    Extraction: {extraction_status}\n")
                    file.write(f"    File: {filename}\n\n")

            print(f"  📋 Created index file: {index_filename}")

        except Exception as e:
            print(f"  ⚠️ Could not create index file: {str(e)}")

    def process_companies(self, companies: list[str], articles_per_company: int = 5):
        """
        Process news for multiple companies with full content extraction.

        Args:
            companies: List of company names
            articles_per_company: Number of articles per company
        """
        print(f"🚀 Starting enhanced news collection for {len(companies)} companies...")
        print(f"📄 Articles per company: {articles_per_company}")
        print("🔧 Full content extraction: ENABLED")
        print("-" * 60)

        for company in companies:
            print(f"\n📰 Processing {company}...")

            # Fetch basic articles
            articles = self.fetch_company_news(company, articles_per_company)

            if articles:
                # Enhance with full content
                enhanced_articles = self.enhance_articles_with_full_content(articles)

                # Save each article to individual files
                self.save_individual_articles(company, enhanced_articles)

            print()  # Add blank line for readability

        print("🎉 Enhanced news collection completed!")


def main():
    """Main function to run the enhanced news fetcher."""
    # Load environment variables
    load_dotenv()

    # Get API key from environment
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key or api_key == "your_newsapi_key_here":
        print("❌ Error: Please set your NewsAPI key in the .env file")
        print("💡 Get your free API key from: https://newsapi.org/register")
        return

    # Define companies to fetch news for
    companies = ["Apple", "Microsoft", "Google", "Amazon", "Tesla"]

    # Initialize enhanced processor and run
    processor = FullNewsProcessor(api_key)
    processor.process_companies(
        companies, articles_per_company=3
    )  # Reduced to 3 for faster processing


if __name__ == "__main__":
    main()
