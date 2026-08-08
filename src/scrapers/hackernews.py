import logging
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import aiohttp
from src.scrapers.base import BaseScraper
from src.shared.models import PostIngestRequest

logger = logging.getLogger("tide.scrapers.hackernews")

class HackerNewsScraper(BaseScraper):
    def __init__(self):
        super().__init__("hackernews")

    async def fetch(self) -> List[Dict[str, Any]]:
        # Fetch top stories from Hacker News public API
        top_stories_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(top_stories_url) as response:
                    if response.status != 200:
                        logger.error(f"Hacker News returned status {response.status}")
                        return []
                    story_ids = await response.json()
                    
                # Limit to the number configured
                target_ids = story_ids[:self.limit]
                
                # Fetch details for each story concurrently
                tasks = [self._fetch_story(session, s_id) for s_id in target_ids]
                stories = await asyncio.gather(*tasks)
                
                # Filter out None and keep only stories (exclude comments/jobs if any, and filter for tech relevance)
                valid_stories = []
                for s in stories:
                    if s and s.get("type") == "story":
                        title = s.get("title", "").lower()
                        # Filter by broad tech keywords to keep it relevant to Tide's beachhead domain
                        keywords = ["ai", "llm", "gpt", "model", "neural", "database", "postgres", "rust", "python", "developer", "agent", "software", "scaling", "open source", "api"]
                        if any(kw in title for kw in keywords):
                            valid_stories.append(s)
                            
                return valid_stories
            except Exception as e:
                logger.error(f"Error fetching from Hacker News: {e}")
                return []

    async def _fetch_story(self, session: aiohttp.ClientSession, story_id: int) -> Optional[Dict[str, Any]]:
        url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            logger.warning(f"Error fetching HN item {story_id}: {e}")
        return None

    def normalize(self, raw_item: Dict[str, Any]) -> PostIngestRequest:
        time_sec = raw_item.get("time", 0)
        published_at = datetime.fromtimestamp(time_sec, timezone.utc) if time_sec else datetime.now(timezone.utc)
        
        score = raw_item.get("score", 0)
        descendants = raw_item.get("descendants", 0) # comment count
        
        engagement = {
            "raw_engagement": score,       # Upvotes
            "raw_authority": score * 0.5,  # Calculated score weight
            "raw_reach": descendants       # Comments as proxy for reach
        }
        
        body = (
            f"Hacker News Story: {raw_item.get('title', '')}\n"
            f"Posted by: {raw_item.get('by', '')}\n"
            f"Score: {score} | Comments: {descendants}\n"
            f"URL: {raw_item.get('url', '')}"
        )

        return PostIngestRequest(
            source="hn",
            source_id=str(raw_item.get("id")),
            title=raw_item.get("title", ""),
            body=body,
            url=raw_item.get("url") or f"https://news.ycombinator.com/item?id={raw_item.get('id')}",
            canonical_url=raw_item.get("url") or f"https://news.ycombinator.com/item?id={raw_item.get('id')}",
            published_at=published_at,
            engagement=engagement,
            native_tags=["hackernews", "show-hn" if raw_item.get("title", "").startswith("Show HN") else "tech"]
        )
