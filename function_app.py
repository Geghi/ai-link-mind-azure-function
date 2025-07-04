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
    logging.info('Python queue trigger function processed a request for recursive scraping.')

    try:
        req_body: dict = json.loads(azqueue.get_body().decode('utf-8'))
    except ValueError:
        logging.error("Invalid JSON payload in queue message.")
        return

    task_id = req_body.get('task_id')
    url = req_body.get('url')
    depth = req_body.get('depth', 0)
    max_depth = req_body.get('max_depth', 2)
    scraped_page_id = req_body.get('scraped_page_id') # Retrieve scraped_page_id from queue message


    if not task_id or not url or scraped_page_id is None:
        logging.error("Missing 'task_id', 'url', or 'scraped_page_id' in queue message.")
        return


    if depth >= max_depth:
        logging.info(f"Max depth reached for {url} at depth {depth}.")
        update_scraped_page_status(task_id, url, "Completed") # Mark as completed if max depth reached
        return

    html_content = get_page_html_content(url)
    if not html_content:
        logging.error(f"Failed to retrieve HTML content for {url}. Skipping further processing.")
        update_scraped_page_status(task_id, url, "Failed")
        return
    
    page_text_content = get_page_text_content(html_content) if html_content else None


    

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
            if i >= len(words): # Ensure we don't go past the end if overlap makes us
                break

        for i, chunk in enumerate(chunks):
            try:
                embedding = get_embedding(chunk)
                insert_text_chunk_with_embedding(scraped_page_id, chunk, embedding)
                logging.info(f"Inserted chunk {i+1}/{len(chunks)} for {url}")
            except Exception as e:
                logging.error(f"Error generating or inserting embedding for chunk {i+1} of {url}: {e}")
    else:
        logging.warning(f"No text content to chunk for {url}.")

    internal_links = get_internal_links(url, url, html_content)
    logging.info(f"Found internal links at {url}: {internal_links}")

    for link in internal_links:
        try:
            # Use the new service to insert/check for duplicates
            if insert_scraped_page(task_id, link, "Queued"):
                
                # Enqueue the next level of scraping
                if depth + 1 < max_depth - 1:
                    next_payload: dict = {"task_id": task_id, "url": link, "depth": depth + 1, "max_depth": max_depth, "scraped_page_id": scraped_page_id}
                    output_queue.set(json.dumps(next_payload))
                else:
                    message_body: str = json.dumps({"task_id": task_id, "url": link, "depth": depth + 1, "scraped_page_id": scraped_page_id})
                    send_message_to_service_bus(sender, message_body)

        except Exception as e:
            logging.error(f"Error processing link {link}: {e}")

    update_scraped_page_status(task_id, url, "Completed")
    logging.info(f"Processed {url} at depth {depth}.")
    time.sleep(5) # Introduce a 5-second delay

@app.route(route="ScrapeUrl", auth_level=func.AuthLevel.FUNCTION)
@app.queue_output(arg_name="output_queue", queue_name="scrape-queue",
                  connection="AzureWebJobsStorage")
def ScrapeUrl(req: func.HttpRequest, output_queue: func.Out[str]) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        req_body: dict = req.get_json()
    except ValueError:
        return json_response("Please pass a JSON payload with 'url' and 'task_id' in the request body.", 400)

    url = req_body.get('url')
    task_id = req_body.get('task_id')
    max_depth = req_body.get('max_depth', 2)

    if not url or not task_id:
        return json_response("Please pass 'url' and 'task_id' in the JSON payload.", 400)

    logging.info(f"Received request for URL: {url}, Task ID: {task_id}")

    try:
        # Insert the base URL into scraped_pages right away and get its ID
        scraped_page_id = insert_scraped_page(task_id, url, "Queued") # Status "Queued" initially
        if scraped_page_id is None:
            return json_response(f"Failed to create initial scraped page entry for {url}.", 500)

        # Send initial message to the queue, including the scraped_page_id
        initial_payload: dict = {"task_id": task_id, "url": url, "depth": 0, "max_depth": max_depth, "scraped_page_id": scraped_page_id}
        output_queue.set(json.dumps(initial_payload))
    except Exception as e:
        logging.error(f"Failed to process initial request for {url}: {e}")
        return json_response(f"Failed to start scraping for {url}.", 500)

    return json_response(f"Initiated scraping for URL: {url}.", 202)
