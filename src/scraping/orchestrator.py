import asyncio
import logging
from typing import List, Set, Dict, Any
import aiohttp
from src.services.scraper_service import ScraperService
from src.services.scraped_pages_service import ScrapedPagesService

logger = logging.getLogger(__name__)

class ScrapingOrchestrator:
    """
    Orchestrates the recursive scraping of a website.
    """

    def __init__(self, scraper_service: ScraperService, scraped_pages_service: ScrapedPagesService):
        self.scraper_service = scraper_service
        self.scraped_pages_service = scraped_pages_service
        self.visited_urls: Set[str] = set()

    async def scrape(self, session: aiohttp.ClientSession, url: str, task_id: str, user_id: str, depth: int, max_depth: int) -> List[Dict[str, Any]]:
        """
        Recursively scrapes a URL, extracts content, and finds internal links.
        """
        if url in self.visited_urls or depth > max_depth:
            return []

        self.visited_urls.add(url)

        scraped_page_id = self.scraped_pages_service.insert_scraped_page(task_id, user_id, url, status="Pending")

        html_content = await self.scraper_service.fetch_page(session, url)
        if not html_content:
            logger.error(f"Failed to fetch content for {url}. Skipping.")
            self.scraped_pages_service.update_scraped_page_status(task_id, url, "Failed")
            return []

        if not scraped_page_id:
            logger.error(f"Failed to create a scraped page record for {url}.")
            return []

        page_text_content = self.scraper_service.get_page_text_content(html_content)
        payloads = []
        if page_text_content:
            self.scraped_pages_service.update_scraped_page_status(task_id, url, "Queued", page_text_content=page_text_content)

            embedding_payload = {
                "scraped_page_id": scraped_page_id,
                "user_id": user_id,
                "task_id": task_id,
                "url": url,
                "page_text_content": page_text_content
            }
            payloads.append(embedding_payload)
            logger.info(f"Prepared {url} for embedding.")
        else:
            self.scraped_pages_service.update_scraped_page_status(task_id, url, "Completed")
            logger.warning(f"No text content found for {url}. Marked as completed.")

        if depth < max_depth:
            internal_links = self.scraper_service.get_internal_links(url, url, html_content)
            tasks = [self.scrape(session, link, task_id, user_id, depth + 1, max_depth) for link in internal_links]
            results = await asyncio.gather(*tasks)
            for result in results:
                payloads.extend(result)

        return payloads
