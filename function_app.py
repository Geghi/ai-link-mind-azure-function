import azure.functions as func
import json
import logging
from azure.functions import Out # Added for queue output binding

from src.services.scraper import get_internal_links, get_page_text_content, get_page_html_content
from src.services.azure_service_bus_service import get_service_bus_sender_and_queue_name, send_message_to_service_bus
from src.services.supabase_service import get_supabase_client
from src.services.scraped_pages_service import insert_scraped_page, update_scraped_page_status, insert_text_chunk_with_embedding
from src.services.openai_service import get_embedding
from src.utils import json_response
import time

app = func.FunctionApp()

supabase = get_supabase_client()
sender, SERVICE_BUS_QUEUE_NAME = get_service_bus_sender_and_queue_name()

@app.queue_trigger(arg_name="azqueue", queue_name="scrape-queue",
                   connection="AzureWebJobsStorage")
@app.queue_output(arg_name="output_queue", queue_name="scrape-queue",
                   connection="AzureWebJobsStorage")
def ScrapeUrlRecursive(azqueue: func.QueueMessage, output_queue: func.Out[str]) -> None:
    """
    Azure Queue Trigger function for recursive web scraping.

    Processes a message from the 'scrape-queue', fetches the URL content,
    generates embeddings, stores chunks, and queues new internal links for further scraping.

    Args:
        azqueue (func.QueueMessage): The message from the Azure Storage Queue.
        output_queue (func.Out[str]): An output binding to send new messages back to the 'scrape-queue'.
    """
    logging.info('Python queue trigger function processed a request for recursive scraping.')

    try:
        req_body: dict = json.loads(azqueue.get_body().decode('utf-8'))
    except ValueError as e:
        logging.error(f"Invalid JSON payload in queue message: {e}", exc_info=True)
        return

    task_id = req_body.get('task_id')
    url = req_body.get('url')
    depth = req_body.get('depth', 0)
    max_depth = req_body.get('max_depth', 2)
    scraped_page_id = req_body.get('scraped_page_id')

    if not all([task_id, url, scraped_page_id is not None]):
        logging.error("Missing 'task_id', 'url', or 'scraped_page_id' in queue message. Cannot process.")
        return

    if depth >= max_depth:
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

    # Chunking and Embedding
    if page_text_content:
        update_scraped_page_status(task_id, url, "Processing", page_text_content=page_text_content)

        # Simple chunking for demonstration. A more robust solution would handle sentence boundaries, etc.
        chunk_size = 500 # words
        overlap_size = 100 # words
        words = page_text_content.split()
        
        chunks = []
        i = 0
        while i < len(words):
            chunk = " ".join(words[i:i + chunk_size])
            chunks.append(chunk)
            i += (chunk_size - overlap_size)
            # Ensure we don't go past the end if overlap makes us
            if i >= len(words) and (len(words) - (i - (chunk_size - overlap_size))) < chunk_size:
                break

        for i, chunk in enumerate(chunks):
            try:
                embedding = get_embedding(chunk)
                insert_text_chunk_with_embedding(scraped_page_id, chunk, embedding)
                logging.info(f"Inserted chunk {i+1}/{len(chunks)} for {url}")
            except Exception as e:
                logging.error(f"Error generating or inserting embedding for chunk {i+1} of {url}: {e}", exc_info=True)
    else:
        logging.warning(f"No text content to chunk for {url}.")

    internal_links = get_internal_links(url, url, html_content)
    logging.info(f"Found internal links at {url}: {internal_links}")

    for link in internal_links:
        try:
            # Use the new service to insert/check for duplicates
            new_scraped_page_id = insert_scraped_page(task_id, link, "Queued")
            if new_scraped_page_id:
                # Enqueue the next level of scraping
                if depth + 1 < max_depth:
                    next_payload: dict = {"task_id": task_id, "url": link, "depth": depth + 1, "max_depth": max_depth, "scraped_page_id": new_scraped_page_id}
                    output_queue.set(json.dumps(next_payload))
                else:
                    # Send to Service Bus to end recursion for this branch
                    message_body: str = json.dumps({"task_id": task_id, "url": link, "depth": depth + 1, "scraped_page_id": new_scraped_page_id})
                    send_message_to_service_bus(sender, message_body)
            else:
                logging.info(f"Link {link} already processed or failed to insert for task {task_id}. Skipping queueing.")

        except Exception as e:
            logging.error(f"Error processing link {link} for task {task_id}: {e}", exc_info=True)

    update_scraped_page_status(task_id, url, "Completed")
    logging.info(f"Processed {url} at depth {depth}. Status: Completed.")

@app.route(route="ScrapeUrl", auth_level=func.AuthLevel.FUNCTION)
@app.queue_output(arg_name="output_queue", queue_name="scrape-queue",
                  connection="AzureWebJobsStorage")
def ScrapeUrl(req: func.HttpRequest, output_queue: func.Out[str]) -> func.HttpResponse:
    """
    Azure HTTP Trigger function to initiate web scraping.

    Receives an HTTP request with a URL and task_id, creates an initial entry in Supabase,
    and sends a message to the 'scrape-queue' to start the recursive scraping process.

    Args:
        req (func.HttpRequest): The HTTP request object.
        output_queue (func.Out[str]): An output binding to send the initial message to the 'scrape-queue'.

    Returns:
        func.HttpResponse: An HTTP response indicating the status of the request.
    """
    logging.info('Python HTTP trigger function processed a request.')

    try:
        req_body: dict = req.get_json()
    except ValueError as e:
        logging.error(f"Invalid JSON payload in HTTP request: {e}", exc_info=True)
        return json_response("Please pass a JSON payload with 'url' and 'task_id' in the request body.", 400)

    url = req_body.get('url')
    task_id = req_body.get('task_id')
    max_depth = req_body.get('max_depth', 2)

    if not all([url, task_id]):
        logging.error("Missing 'url' or 'task_id' in HTTP request payload.")
        return json_response("Please pass 'url' and 'task_id' in the JSON payload.", 400)

    logging.info(f"Received request for URL: {url}, Task ID: {task_id}")

    try:
        # Insert the base URL into scraped_pages right away and get its ID
        scraped_page_id = insert_scraped_page(task_id, url, "Queued") # Status "Queued" initially
        if scraped_page_id is None:
            logging.error(f"Failed to create initial scraped page entry for {url} for task {task_id}.")
            return json_response(f"Failed to create initial scraped page entry for {url}.", 500)

        # Send initial message to the queue, including the scraped_page_id
        initial_payload: dict = {"task_id": task_id, "url": url, "depth": 0, "max_depth": max_depth, "scraped_page_id": scraped_page_id}
        output_queue.set(json.dumps(initial_payload))
    except Exception as e:
        logging.error(f"Failed to process initial request for {url} for task {task_id}: {e}", exc_info=True)
        return json_response(f"Failed to start scraping for {url}.", 500)

    return json_response(f"Initiated scraping for URL: {url}.", 202)
