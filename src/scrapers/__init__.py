import asyncio
import logging
from src.scrapers.github import GitHubScraper
from src.scrapers.arxiv import ArxivScraper
from src.scrapers.hackernews import HackerNewsScraper
from src.scrapers.stackoverflow import StackOverflowScraper
from src.scrapers.newsapi import NewsApiScraper

logger = logging.getLogger("tide.scrapers")

SCRAPERS = {
    "github": GitHubScraper,
    "arxiv": ArxivScraper,
    "hackernews": HackerNewsScraper,
    "stackoverflow": StackOverflowScraper,
    "newsapi": NewsApiScraper
}

async def run_all_scrapers():
    """Runs all enabled scrapers concurrently."""
    logger.info("Initializing run of all enabled scrapers...")
    tasks = []
    
    for name, scraper_class in SCRAPERS.items():
        scraper = scraper_class()
        if scraper.enabled:
            tasks.append(scraper.run())
        else:
            logger.info(f"Scraper '{name}' is disabled in config.")
            
    if tasks:
        await asyncio.gather(*tasks)
        logger.info("All scraper runs completed.")
    else:
        logger.warning("No scrapers are currently enabled.")
