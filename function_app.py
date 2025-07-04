import azure.functions as func
import json
import logging
from azure.functions import Out # Added for queue output binding

from src.services.scraper import get_internal_links
from src.services.azure_service_bus_service import get_service_bus_sender_and_queue_name, send_message_to_service_bus
from src.services.supabase_service import get_supabase_client
from src.services.scraped_pages_service import insert_scraped_page # Added import
from src.utils import json_response

app = func.FunctionApp()

supabase = get_supabase_client()
sender, SERVICE_BUS_QUEUE_NAME = get_service_bus_sender_and_queue_name()

@app.queue_trigger(arg_name="azqueue", queue_name="scrape-queue",
                   connection="AzureWebJobsStorage")
@app.queue_output(arg_name="outputQueue", queue_name="scrape-queue",
                  connection="AzureWebJobsStorage")
def ScrapeUrlRecursive(azqueue: func.QueueMessage, outputQueue: func.Out[str]):
    logging.info('Python queue trigger function processed a request for recursive scraping.')

    try:
        req_body = json.loads(azqueue.get_body().decode('utf-8'))
    except ValueError:
        logging.error("Invalid JSON payload in queue message.")
        return

    task_id = req_body.get('task_id')
    url = req_body.get('url')
    depth = req_body.get('depth', 0)
    max_depth = req_body.get('max_depth', 2)

    if not task_id or not url:
        logging.error("Missing 'task_id' or 'url' in queue message.")
        return

    if depth >= max_depth:
        logging.info(f"Max depth reached for {url} at depth {depth}.")
        return

    internal_links = get_internal_links(url, url)
    logging.info(f"Found {len(internal_links)} internal links at {url}.")

    for link in internal_links:
        try:
            # Use the new service to insert/check for duplicates
            if insert_scraped_page(task_id, link, "Queued"):
                message_body = json.dumps({"task_id": task_id, "url": link, "depth": depth})
                send_message_to_service_bus(sender, message_body)
                
                # Enqueue the next level of scraping
                if depth + 1 < max_depth:
                    next_payload = {"task_id": task_id, "url": link, "depth": depth + 1, "max_depth": max_depth}
                    outputQueue.set(json.dumps(next_payload))
        except Exception as e:
            logging.error(f"Error processing link {link}: {e}")

    logging.info(f"Processed {url} at depth {depth}.")

@app.route(route="ScrapeUrl", auth_level=func.AuthLevel.FUNCTION)
@app.queue_output(arg_name="outputQueue", queue_name="scrape-queue",
                  connection="AzureWebJobsStorage")
def ScrapeUrl(req: func.HttpRequest, outputQueue: func.Out[str]) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        req_body = req.get_json()
    except ValueError:
        return json_response("Please pass a JSON payload with 'url' and 'task_id' in the request body.", 400)

    url = req_body.get('url')
    task_id = req_body.get('task_id')
    max_depth = req_body.get('max_depth', 2)

    if not url or not task_id:
        return json_response("Please pass 'url' and 'task_id' in the JSON payload.", 400)

    logging.info(f"Received request for URL: {url}, Task ID: {task_id}")

    try:
        # Insert the base URL into scraped_pages right away
        insert_scraped_page(task_id, url, "Completed")

        # Send initial message to the queue
        initial_payload = {"task_id": task_id, "url": url, "depth": 0, "max_depth": max_depth}
        outputQueue.set(json.dumps(initial_payload))
    except Exception as e:
        logging.error(f"Failed to process initial request for {url}: {e}")
        return json_response(f"Failed to start scraping for {url}.", 500)

    return json_response(f"Initiated scraping for URL: {url}.", 202)
