import json
import logging
import azure.functions as func
from azure.functions import Out
from src.services.scraped_pages_service import insert_scraped_page, get_scraped_urls_for_task

import tiktoken
from typing import List, Dict

def count_tokens(messages: List[Dict[str, str]], model: str = "gpt-3.5-turbo") -> int:
    """
    Counts the number of tokens in a list of messages for a given OpenAI model.
    Based on OpenAI's cookbook example for counting tokens.

    Args:
        messages (List[Dict[str, str]]): A list of message dictionaries,
                                          each with 'role' and 'content' keys.
        model (str): The name of the OpenAI model to use for tokenization.

    Returns:
        int: The total number of tokens in the messages.
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base") # Fallback for unknown models

    if model == "gpt-3.5-turbo":
        # gpt-3.5-turbo-0301 has the same tokenization as gpt-4-0314
        # Every message follows <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_message = 4
        tokens_per_name = -1  # If there's a name, role is omitted
    elif model == "gpt-4":
        tokens_per_message = 3
        tokens_per_name = 1
    else:
        # Fallback for other models, might not be perfectly accurate
        tokens_per_message = 3
        tokens_per_name = 1

    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # Every reply is primed with <|start|>assistant<|message|>
    return num_tokens


def json_response(message: str, status_code: int) -> func.HttpResponse:
    """
    Creates a JSON HTTP response.
    """
    return func.HttpResponse(
        json.dumps({"message": message}),
        mimetype="application/json",
        status_code=status_code
    )

def parse_queue_message(azqueue: func.QueueMessage) -> dict | None:
    """Helper to parse and validate queue message payload."""
    try:
        req_body: dict = json.loads(azqueue.get_body().decode('utf-8'))
    except ValueError as e:
        logging.error(f"Invalid JSON payload in queue message: {e}", exc_info=True)
        return None

    task_id = req_body.get('task_id')
    url = req_body.get('url')
    user_id = req_body.get('user_id') # New: Get user_id from queue message
    depth = req_body.get('depth', 0)
    max_depth = req_body.get('max_depth', 2)
    scraped_page_id = req_body.get('scraped_page_id')

    if not all([task_id, url, user_id, scraped_page_id is not None]): # New: user_id is now required
        logging.error("Missing 'task_id', 'url', 'user_id', or 'scraped_page_id' in queue message. Cannot process.")
        return None
    
    return {"task_id": task_id, "url": url, "user_id": user_id, "depth": depth, "max_depth": max_depth, "scraped_page_id": scraped_page_id}

def process_internal_links(task_id: str, user_id: str, current_url: str, depth: int, max_depth: int, internal_links: list[str], output_queue: func.Out[str]) -> None:
    """
    Processes internal links found on a page, queues them for scraping if they are new.
    Relies on the database's unique constraint on (task_id, url) to avoid race conditions.
    """
    if depth >= max_depth:
        logging.info(f"Max depth reached at {current_url}. No further links will be queued from this page.")
        return

    messages_to_queue = []
    visited_urls = set()  # Keep track of URLs processed in this batch

    for link in internal_links:
        # Normalize the URL by removing the trailing slash if it exists
        normalized_link = link.rstrip('/')
        
        if normalized_link in visited_urls:
            continue  # Skip if we've already processed this normalized link in the current batch
            
        visited_urls.add(normalized_link)

        try:
            # Attempt to insert the new link. The function will return an ID only if the link is new.
            new_scraped_page_id = insert_scraped_page(task_id, user_id, normalized_link, "Queued")
            
            if new_scraped_page_id:
                # If an ID is returned, the link was new, so we can queue it for scraping.
                logging.info(f"New link found and inserted: {link}. Queueing for scraping.")
                next_payload = {
                    "task_id": task_id,
                    "url": link,
                    "user_id": user_id,
                    "depth": depth + 1,
                    "max_depth": max_depth,
                    "scraped_page_id": new_scraped_page_id
                }
                messages_to_queue.append(next_payload)
            else:
                # If None is returned, the link already existed, so we don't queue it again.
                logging.info(f"Link {link} already exists for task {task_id}. Skipping.")

        except Exception as e:
            logging.error(f"Error processing link {link} for task {task_id}: {e}", exc_info=True)

    if messages_to_queue:
        logging.info(f"Queueing {len(messages_to_queue)} new internal links for task {task_id}.")
        # Note: Azure Functions Python worker currently sends each item in a list as a separate message.
        output_queue.set(json.dumps(messages_to_queue))

def parse_http_request(req: func.HttpRequest) -> dict | func.HttpResponse:
    """Helper to parse and validate HTTP request payload."""
    try:
        req_body: dict = req.get_json()
    except ValueError as e:
        logging.error(f"Invalid JSON payload in HTTP request: {e}", exc_info=True)
        return json_response("Please pass a JSON payload with 'url' and 'task_id' in the request body.", 400)

    url = req_body.get('url')
    task_id = req_body.get('task_id')
    user_id = req_body.get('user_id') # New: Get user_id from request
    max_depth = req_body.get('max_depth', 2)

    if not all([url, task_id, user_id]): # New: user_id is now required
        logging.error("Missing 'url', 'task_id', or 'user_id' in HTTP request payload.")
        return json_response("Please pass 'url', 'task_id', and 'user_id' in the JSON payload.", 400)
    
    return {"url": url, "task_id": task_id, "user_id": user_id, "max_depth": max_depth}
