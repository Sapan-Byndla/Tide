import logging
from datetime import datetime, timezone
from typing import List, Dict, Any
import aiohttp
from src.scrapers.base import BaseScraper
from src.shared.models import PostIngestRequest

logger = logging.getLogger("tide.scrapers.github")

class GitHubScraper(BaseScraper):
    def __init__(self):
        super().__init__("github")
        self.headers = {"User-Agent": "Tide-App-Scraper"}
        token = self.scraper_config.get("token")
        if token:
            self.headers["Authorization"] = f"token {token}"

    async def fetch(self) -> List[Dict[str, Any]]:
        # Fetch trending/popular repositories created in the last 7 days containing AI tags
        # Public search API
        url = "https://api.github.com/search/repositories"
        params = {
            "q": "ai OR machine-learning OR llm",
            "sort": "stars",
            "order": "desc",
            "per_page": min(self.limit, 100)
        }
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        err_text = await response.text()
                        logger.error(f"GitHub API returned status {response.status}: {err_text}")
                        return []
                    data = await response.json()
                    return data.get("items", [])
            except Exception as e:
                logger.error(f"Error fetching from GitHub: {e}")
                return []

    def normalize(self, raw_item: Dict[str, Any]) -> PostIngestRequest:
        # Normalize repository data into PostIngestRequest
        published_at_str = raw_item.get("created_at")
        published_at = datetime.fromisoformat(published_at_str.replace("Z", "+00:00")) if published_at_str else datetime.now(timezone.utc)
        
        topics = raw_item.get("topics", [])
        
        body = (
            f"Description: {raw_item.get('description', '')}\n"
            f"Primary Language: {raw_item.get('language', 'None')}\n"
            f"Stars: {raw_item.get('stargazers_count', 0)} | Forks: {raw_item.get('forks_count', 0)}"
        )
        
        engagement = {
            "raw_engagement": raw_item.get("stargazers_count", 0), # stars as proxy
            "raw_authority": raw_item.get("watchers_count", 0),
            "raw_reach": raw_item.get("forks_count", 0)
        }

        return PostIngestRequest(
            source="github",
            source_id=str(raw_item.get("id")),
            title=raw_item.get("full_name", ""),
            body=body,
            url=raw_item.get("html_url", ""),
            canonical_url=raw_item.get("html_url", ""),
            published_at=published_at,
            engagement=engagement,
            native_tags=topics
        )
