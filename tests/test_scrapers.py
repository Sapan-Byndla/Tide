import sys
import os
import asyncio
from datetime import datetime

# Adjust path to import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.scrapers.arxiv import ArxivScraper
from src.scrapers.hackernews import HackerNewsScraper
from src.scrapers.github import GitHubScraper
from src.scrapers.stackoverflow import StackOverflowScraper

async def test_scraper(name, scraper_instance):
    print(f"\n--- Testing Scraper: {name} ---")
    try:
        print(f"Fetching raw items from {name}...")
        raw_items = await scraper_instance.fetch()
        print(f"Successfully fetched {len(raw_items)} items.")
        
        if not raw_items:
            print(f"Warning: No items returned from {name}. It might be rate-limited or the API endpoint structure changed.")
            return False

        first_item = raw_items[0]
        print(f"Normalizing first item...")
        normalized = scraper_instance.normalize(first_item)
        
        print(f"Normalized Post successfully:")
        print(f"  Source: {normalized.source}")
        print(f"  Source ID: {normalized.source_id}")
        print(f"  Title: {normalized.title}")
        print(f"  Body length: {len(normalized.body or '')} chars")
        print(f"  URL: {normalized.url}")
        print(f"  Published At: {normalized.published_at}")
        print(f"  Engagement: {normalized.engagement}")
        print(f"  Native Tags: {normalized.native_tags}")
        
        return True
    except Exception as e:
        print(f"Error testing scraper {name}: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("Starting scraper verification tests...")
    
    scrapers = {
        "arxiv": ArxivScraper(),
        "hackernews": HackerNewsScraper(),
        "github": GitHubScraper(),
        "stackoverflow": StackOverflowScraper()
    }
    
    results = {}
    for name, instance in scrapers.items():
        # Force enable for test validation
        instance.enabled = True
        success = await test_scraper(name, instance)
        results[name] = success
        
    print("\n=== Scraper Test Results Summary ===")
    for name, success in results.items():
        status = "PASSED" if success else "FAILED/WARNING"
        print(f"  Scraper '{name}': {status}")

if __name__ == "__main__":
    asyncio.run(main())
