import azure.functions as func
import logging
import json
import os

from src.services.scraped_pages_service import insert_scraped_page, update_scraped_page_status
from src.services.scraper import get_internal_links, get_page_text_content, get_page_html_content
from src.utils import json_response, process_internal_links, parse_http_request

# Configure logging
logging.basicConfig(level=logging.INFO)
logging.getLogger().setLevel(logging.INFO)

# Create a blueprint for HTTP triggered scraping
scrape_url_bp = func.Blueprint()

@scrape_url_bp.route(route="ScrapeUrl", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
@scrape_url_bp.queue_output(arg_name="output_queue", queue_name="scrape-queue",
                            connection="AzureWebJobsStorage")
def ScrapeUrl(req: func.HttpRequest, output_queue: func.Out[str]) -> func.HttpResponse:
    """
    Azure HTTP Trigger function to initiate web scraping.
    """
    try:
        logging.info('ScrapeUrl HTTP trigger function processed a request.')
        logging.info(f"Request body: {req.get_body().decode('utf-8')}")

        payload = parse_http_request(req)
        if isinstance(payload, func.HttpResponse):
            return payload # Return error response if parsing failed

        url = payload['url']
        task_id = payload['task_id']
        user_id = payload['user_id']
        max_depth = payload['max_depth']

        logging.info(f"Received request for URL: {url}, Task ID: {task_id}, User ID: {user_id}")

        try:
            scraped_page_id = insert_scraped_page(task_id, user_id, url, "Queued")
            if scraped_page_id is None:
                logging.error(f"Failed to create initial scraped page entry for {url} for task {task_id}, user {user_id}.")
                return json_response(f"Failed to create initial scraped page entry for {url}.", 500)

            initial_payload: dict = {"task_id": task_id, "url": url, "user_id": user_id, "depth": 0, "max_depth": max_depth, "scraped_page_id": scraped_page_id}
            output_queue.set(json.dumps(initial_payload))
        except Exception as e:
            logging.error(f"Failed to process initial request for {url} for task {task_id}, user {user_id}: {e}", exc_info=True)
            return json_response(f"Failed to start scraping for {url}.", 500)
        return json_response(f"Initiated scraping for URL: {url}.", 202)
    except Exception as e:
        logging.error(f"Error processing request: {e}", exc_info=True)
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )
