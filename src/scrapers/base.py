import abc
import logging
from typing import List, Dict, Any
import aiohttp
from src.shared.models import PostIngestRequest
from src.config import config

logger = logging.getLogger("tide.scrapers.base")

class BaseScraper(abc.ABC):
    """Abstract base class for all source fetchers in the Tide system."""

    def __init__(self, name: str):
        self.name = name
        self.scraper_config = config.get_scraper_config(name)
        self.enabled = self.scraper_config.get("enabled", False)
        self.limit = self.scraper_config.get("limit", 50)
        self.ingest_url = f"http://{config.ingest_host}:{config.ingest_port}/ingest"

    @abc.abstractmethod
    async def fetch(self) -> List[Dict[str, Any]]:
        """Fetches raw data posts from the source API."""
        pass

    @abc.abstractmethod
    def normalize(self, raw_item: Dict[str, Any]) -> PostIngestRequest:
        """Normalizes a raw API item into the standard PostIngestRequest structure."""
        pass

    async def run(self):
        """Runs the fetch-normalize-ingest pipeline for this scraper."""
        if not self.enabled:
            logger.info(f"Scraper '{self.name}' is disabled.")
            return

        logger.info(f"Starting scraper '{self.name}' (Limit: {self.limit})...")
        try:
            raw_items = await self.fetch()
            logger.info(f"Fetched {len(raw_items)} raw items from '{self.name}'")

            normalized_posts = []
            for item in raw_items:
                try:
                    norm = self.normalize(item)
                    normalized_posts.append(norm)
                except Exception as e:
                    logger.error(f"Failed to normalize item from '{self.name}': {e}")

            logger.info(f"Normalized {len(normalized_posts)} posts from '{self.name}'. Pushing to ingest service...")
            
            async with aiohttp.ClientSession() as session:
                success_count = 0
                for post in normalized_posts:
                    try:
                        # Send post to ingest API
                        async with session.post(
                            self.ingest_url,
                            json=post.model_dump(mode='json'),
                            headers={"Content-Type": "application/json"}
                        ) as resp:
                            if resp.status in (200, 201):
                                success_count += 1
                            else:
                                text = await resp.text()
                                logger.warning(f"Failed to ingest post {post.source_id}: {resp.status} - {text}")
                    except Exception as e:
                        logger.error(f"HTTP error pushing post to ingest: {e}")
                
                logger.info(f"Ingested {success_count}/{len(normalized_posts)} posts successfully from '{self.name}'.")
        except Exception as e:
            logger.exception(f"Unhandled error in scraper '{self.name}' run: {e}")
