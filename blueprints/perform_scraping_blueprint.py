import asyncio
import logging
import json
from typing import List, Set, Dict, Any

import aiohttp
import azure.functions as func
import nest_asyncio

from src.scraping.async_scraper import fetch_page
from src.services.scraped_pages_service import insert_scraped_page, update_scraped_page_status, get_scraped_urls_for_task
from src.services.scraper import get_page_text_content, get_internal_links

# Apply nest_asyncio to allow running asyncio event loop in Azure Functions
nest_asyncio.apply()

# Blueprint for the new scraping endpoint
perform_scraping_bp = func.Blueprint()

async def process_single_url(session: aiohttp.ClientSession, url: str, task_id: str, user_id: str, depth: int, max_depth: int, visited_urls: Set[str]) -> List[Dict[str, Any]]:
    """
    Fetches a single URL, extracts content, finds internal links, and returns payloads for embedding.
    """
    if url in visited_urls or depth > max_depth:
        return []

    visited_urls.add(url)
    
    scraped_page_id = insert_scraped_page(task_id, user_id, url, status="Pending")

    html_content = await fetch_page(session, url)
    if not html_content:
        logging.error(f"Failed to fetch content for {url}. Skipping.")
        insert_scraped_page(task_id, user_id, url, status="Failed")
        return []

    if not scraped_page_id:
        logging.error(f"Failed to create a scraped page record for {url}.")
        return []

    page_text_content = get_page_text_content(html_content)
    payloads = []
    if page_text_content:
        update_scraped_page_status(task_id, url, "Queued", page_text_content=page_text_content)
        
        embedding_payload = {
            "scraped_page_id": scraped_page_id,
            "user_id": user_id,
            "task_id": task_id,
            "url": url,
            "page_text_content": page_text_content
        }
        payloads.append(embedding_payload)
        logging.info(f"Prepared {url} for embedding.")
    else:
        update_scraped_page_status(task_id, url, "Completed")
        logging.warning(f"No text content found for {url}. Marked as completed.")

    # Recursive scraping
    if depth < max_depth:
        internal_links = get_internal_links(url, url, html_content)
        tasks = [process_single_url(session, link, task_id, user_id, depth + 1, max_depth, visited_urls) for link in internal_links]
        results = await asyncio.gather(*tasks)
        for result in results:
            payloads.extend(result)
            
    return payloads


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

    visited_urls = set(get_scraped_urls_for_task(task_id, user_id))
    
    payloads_to_queue = []
    async with aiohttp.ClientSession() as session:
        payloads_to_queue = await process_single_url(session, url, task_id, user_id, 0, max_depth, visited_urls)
    
    if payloads_to_queue:
        embedding_queue.set([json.dumps(p) for p in payloads_to_queue])
        logging.info(f"Queued {len(payloads_to_queue)} pages for embedding.")

    return func.HttpResponse(
        f"Scraping task {task_id} initiated for {url} up to depth {max_depth}. "
        f"Found and queued {len(payloads_to_queue)} pages for embedding.",
        status_code=202
    )
