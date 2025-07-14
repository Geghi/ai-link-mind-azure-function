import json
import logging
import azure.functions as func
from azure.functions import Out

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
