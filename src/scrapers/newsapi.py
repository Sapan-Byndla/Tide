import logging
from datetime import datetime, timezone
from typing import List, Dict, Any
import aiohttp
from src.scrapers.base import BaseScraper
from src.shared.models import PostIngestRequest

logger = logging.getLogger("tide.scrapers.newsapi")

class NewsApiScraper(BaseScraper):
    def __init__(self):
        super().__init__("newsapi")
        self.api_key = self.scraper_config.get("api_key", "")

    async def fetch(self) -> List[Dict[str, Any]]:
        if not self.api_key:
            logger.warning("NewsAPI scraper API key is not configured. Skipping fetch.")
            return []
            
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": "artificial intelligence OR machine learning OR LLM OR database",
            "sortBy": "publishedAt",
            "language": "en",
            "pageSize": min(self.limit, 100),
            "apiKey": self.api_key
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        err_text = await response.text()
                        logger.error(f"NewsAPI returned status {response.status}: {err_text}")
                        return []
                    data = await response.json()
                    return data.get("articles", [])
            except Exception as e:
                logger.error(f"Error fetching from NewsAPI: {e}")
                return []

    def normalize(self, raw_item: Dict[str, Any]) -> PostIngestRequest:
        pub_str = raw_item.get("publishedAt")
        published_at = datetime.fromisoformat(pub_str.replace("Z", "+00:00")) if pub_str else datetime.now(timezone.utc)
        
        source_name = raw_item.get("source", {}).get("name", "Unknown News Source")
        
        body = (
            f"Source: {source_name}\n"
            f"Description: {raw_item.get('description', '')}\n"
            f"Content: {raw_item.get('content', '')}"
        )
        
        # NewsAPI has no native tags, but we can tag with news and source
        tags = ["news", source_name.lower().replace(" ", "-")]

        # Use title and source as unique identifier
        import hashlib
        title = raw_item.get("title", "")
        unique_id = hashlib.md5(f"{title}_{pub_str}".encode("utf-8")).hexdigest()

        return PostIngestRequest(
            source="newsapi",
            source_id=unique_id,
            title=title,
            body=body,
            url=raw_item.get("url"),
            canonical_url=raw_item.get("url"),
            published_at=published_at,
            engagement={},
            native_tags=tags
        )
