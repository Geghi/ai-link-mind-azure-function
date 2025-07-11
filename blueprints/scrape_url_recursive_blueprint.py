import azure.functions as func
import logging
import json
import sys
import os

from src.services.scraped_pages_service import update_scraped_page_status
from src.services.scraper import get_internal_links, get_page_text_content, get_page_html_content
from src.services.embedding_service import process_and_embed_text
from src.utils import parse_queue_message, process_internal_links

# Configure logging
logging.basicConfig(level=logging.INFO)
logging.getLogger().setLevel(logging.INFO)

# Create a blueprint for queue triggered recursive scraping
scrape_url_recursive_bp = func.Blueprint()

@scrape_url_recursive_bp.queue_trigger(arg_name="azqueue", queue_name="scrape-queue",
                                       connection="AzureWebJobsStorage")
@scrape_url_recursive_bp.queue_output(arg_name="output_queue", queue_name="scrape-queue",
                                      connection="AzureWebJobsStorage")
def ScrapeUrlRecursive(azqueue: func.QueueMessage, output_queue: func.Out[str]) -> None:
    """
    Azure Queue Trigger function for recursive web scraping.
    """
    logging.info('ScrapeUrlRecursive queue trigger function processed a request.')
    logging.info(f"Queue message body: {azqueue.get_body().decode('utf-8')}")
    payload = parse_queue_message(azqueue)
    if not payload:
        return
    
    task_id = payload['task_id']
    url = payload['url']
    user_id = payload['user_id']
    depth = payload['depth']
    max_depth = payload['max_depth']
    scraped_page_id = payload['scraped_page_id']

    if depth > max_depth:
        logging.info(f"Max depth reached for {url} at depth {depth}. Marking as completed.")
        update_scraped_page_status(task_id, url, "Completed")
        return

    html_content = get_page_html_content(url)
    if not html_content:
        logging.error(f"Failed to retrieve HTML content for {url}. Skipping further processing.", exc_info=True)
        update_scraped_page_status(task_id, url, "Failed")
        return
    
    page_text_content = get_page_text_content(html_content)
    logging.info(f"Fetched content for {url}. Length: {len(page_text_content)} characters.")

    if page_text_content:
        update_scraped_page_status(task_id, url, "Processing", page_text_content=page_text_content)
        process_and_embed_text(scraped_page_id, user_id, page_text_content, task_id, url)
    else:
        logging.warning(f"No text content to chunk for {url}.")
    
    internal_links = get_internal_links(url, url, html_content)
    logging.info(f"Found internal links at {url}: {internal_links}")

    if internal_links:
        process_internal_links(task_id, user_id, url, depth, max_depth, internal_links, output_queue)

    update_scraped_page_status(task_id, url, "Completed")
    logging.info(f"Processed {url} at depth {depth}. Status: Completed.")
