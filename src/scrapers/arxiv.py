import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import List, Dict, Any
import aiohttp
from src.scrapers.base import BaseScraper
from src.shared.models import PostIngestRequest

logger = logging.getLogger("tide.scrapers.arxiv")

class ArxivScraper(BaseScraper):
    def __init__(self):
        super().__init__("arxiv")

    async def fetch(self) -> List[Dict[str, Any]]:
        # Fetch computer science / AI papers from arXiv API
        url = "http://export.arxiv.org/api/query"
        params = {
            "search_query": "cat:cs.AI OR cat:cs.CL OR cat:cs.LG", # AI, Computation & Language, Machine Learning
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": min(self.limit, 100)
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        logger.error(f"arXiv API returned status {response.status}")
                        return []
                    xml_data = await response.read()
                    return self._parse_xml(xml_data)
            except Exception as e:
                logger.error(f"Error fetching from arXiv: {e}")
                return []

    def _parse_xml(self, xml_data: bytes) -> List[Dict[str, Any]]:
        root = ET.fromstring(xml_data)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        
        items = []
        for entry in root.findall('atom:entry', ns):
            # Extract id
            id_val = entry.find('atom:id', ns).text.strip() if entry.find('atom:id', ns) is not None else ""
            # Canonical ID is the arxiv ID in the URL, e.g. "http://arxiv.org/abs/2401.00001v1" -> "2401.00001"
            arxiv_id = id_val.split('/abs/')[-1].split('v')[0] if '/abs/' in id_val else id_val
            
            title = entry.find('atom:title', ns).text.strip() if entry.find('atom:title', ns) is not None else ""
            # Clean newlines from title
            title = " ".join(title.split())
            
            summary = entry.find('atom:summary', ns).text.strip() if entry.find('atom:summary', ns) is not None else ""
            summary = " ".join(summary.split())
            
            published_str = entry.find('atom:published', ns).text.strip() if entry.find('atom:published', ns) is not None else ""
            
            # Categories
            categories = []
            for cat in entry.findall('atom:category', ns):
                term = cat.get('term')
                if term:
                    categories.append(term)
                    
            url = id_val
            # Find pdf link if possible
            for link in entry.findall('atom:link', ns):
                if link.get('title') == 'pdf':
                    url = link.get('href')
                    break

            items.append({
                "id": arxiv_id,
                "title": title,
                "summary": summary,
                "url": url,
                "canonical_url": f"https://arxiv.org/abs/{arxiv_id}",
                "published_at": published_str,
                "categories": categories
            })
        return items

    def normalize(self, raw_item: Dict[str, Any]) -> PostIngestRequest:
        pub_str = raw_item.get("published_at")
        # Format: "2024-01-01T12:00:00Z"
        published_at = datetime.fromisoformat(pub_str.replace("Z", "+00:00")) if pub_str else datetime.now(timezone.utc)
        
        return PostIngestRequest(
            source="arxiv",
            source_id=raw_item.get("id"),
            title=raw_item.get("title"),
            body=raw_item.get("summary"),
            url=raw_item.get("url"),
            canonical_url=raw_item.get("canonical_url"),
            published_at=published_at,
            engagement={}, # academic papers don't have instant engagement metrics on feed
            native_tags=raw_item.get("categories", [])
        )
