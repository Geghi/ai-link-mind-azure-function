import logging
import json
from typing import List
import aiohttp
import azure.functions as func
import nest_asyncio
from src.scraping.orchestrator import ScrapingOrchestrator
from src.services.scraped_pages_service import ScrapedPagesService
from src.services.scraper_service import ScraperService

# Apply nest_asyncio to allow running asyncio event loop in Azure Functions
nest_asyncio.apply()

# Blueprint for the new scraping endpoint
perform_scraping_bp = func.Blueprint()

@perform_scraping_bp.route(route="scrape", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
@perform_scraping_bp.queue_output(arg_name="embedding_queue", queue_name="embedding-queue", connection="AzureWebJobsStorage")
async def perform_scraping(req: func.HttpRequest, embedding_queue: func.Out[List[str]]) -> func.HttpResponse:
    """
    An HTTP-triggered function that scrapes a URL recursively up to a max depth
    and queues the content for embedding.
    """
    logging.info("Scraping request received.")
    
    try:
        req_body = req.get_json()
        url = req_body.get("url")
        user_id = req_body.get("user_id")
        task_id = req_body.get("task_id")
        max_depth = req_body.get("max_depth", 2)
        
        if not all([url, user_id, task_id]):
            return func.HttpResponse(
                "Please provide 'url', 'user_id', and 'task_id' in the request body.",
                status_code=400
            )
    except ValueError:
        return func.HttpResponse("Invalid JSON format.", status_code=400)

    logging.info(f"Starting scraping task with ID: {task_id} for URL: {url}")

    scraper_service = ScraperService()
    await scraper_service.initialize()
    scraped_pages_service = ScrapedPagesService()
    orchestrator = ScrapingOrchestrator(scraper_service, scraped_pages_service)
    
    payloads_to_queue = []
    async with aiohttp.ClientSession() as session:
        # Get already visited URLs
        orchestrator.visited_urls = scraped_pages_service.get_scraped_urls_for_task(task_id, user_id)
        payloads_to_queue = await orchestrator.scrape(session, url, task_id, user_id, 0, max_depth)
    
    if payloads_to_queue:
        embedding_queue.set([json.dumps(p) for p in payloads_to_queue])
        logging.info(f"Queued {len(payloads_to_queue)} pages for embedding.")

    return func.HttpResponse(
        f"Scraping task {task_id} initiated for {url} up to depth {max_depth}. "
        f"Found and queued {len(payloads_to_queue)} pages for embedding.",
        status_code=202
    )
