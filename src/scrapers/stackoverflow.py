import logging
from datetime import datetime, timezone
from typing import List, Dict, Any
import aiohttp
from src.scrapers.base import BaseScraper
from src.shared.models import PostIngestRequest

logger = logging.getLogger("tide.scrapers.stackoverflow")

class StackOverflowScraper(BaseScraper):
    def __init__(self):
        super().__init__("stackoverflow")

    async def fetch(self) -> List[Dict[str, Any]]:
        # Fetch recent questions tagged with relevant keywords from StackOverflow API
        url = "https://api.stackexchange.com/2.3/questions"
        params = {
            "order": "desc",
            "sort": "creation",
            "tagged": "fastapi",
            "site": "stackoverflow",
            "pagesize": min(self.limit, 100),
            "filter": "default" # includes body if using custom filters, but default gets title and tags
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        err_text = await response.text()
                        logger.error(f"StackOverflow API returned status {response.status}: {err_text}")
                        return []
                    data = await response.json()
                    return data.get("items", [])
            except Exception as e:
                logger.error(f"Error fetching from StackOverflow: {e}")
                return []

    def normalize(self, raw_item: Dict[str, Any]) -> PostIngestRequest:
        creation_date = raw_item.get("creation_date", 0)
        published_at = datetime.fromtimestamp(creation_date, timezone.utc) if creation_date else datetime.now(timezone.utc)
        
        tags = raw_item.get("tags", [])
        score = raw_item.get("score", 0)
        views = raw_item.get("view_count", 0)
        answers = raw_item.get("answer_count", 0)
        
        body = (
            f"Stack Overflow Question: {raw_item.get('title', '')}\n"
            f"Tags: {', '.join(tags)}\n"
            f"Views: {views} | Answers: {answers} | Score: {score}\n"
            f"Link: {raw_item.get('link', '')}"
        )
        
        engagement = {
            "raw_engagement": views,          # Views as proxy for reach
            "raw_authority": score,           # Question score
            "raw_reach": answers              # Answers count
        }

        # StackExchange API returns HTML entities in title like &#39; so decode them if needed
        import html
        title = html.unescape(raw_item.get("title", ""))

        return PostIngestRequest(
            source="stackoverflow",
            source_id=str(raw_item.get("question_id")),
            title=title,
            body=body,
            url=raw_item.get("link", ""),
            canonical_url=raw_item.get("link", ""),
            published_at=published_at,
            engagement=engagement,
            native_tags=tags
        )
