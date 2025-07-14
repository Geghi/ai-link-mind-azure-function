import logging
import json
import azure.functions as func
from src.services.embedding_service import EmbeddingService
from src.services.scraped_pages_service import ScrapedPagesService

# Blueprint for the embedding queue trigger
embedding_bp = func.Blueprint()

@embedding_bp.queue_trigger(arg_name="msg", queue_name="embedding-queue",
                             connection="AzureWebJobsStorage")
def process_embedding_queue(msg: func.QueueMessage) -> None:
    """
    Processes messages from the embedding queue to generate and store embeddings.
    """
    logging.info(f"Processing message from embedding queue: {msg.get_body().decode('utf-8')}")
    
    try:
        payload = json.loads(msg.get_body().decode('utf-8'))
        scraped_page_id = payload['scraped_page_id']
        user_id = payload['user_id']
        task_id = payload['task_id']
        url = payload['url']
        page_text_content = payload['page_text_content']
    except (json.JSONDecodeError, KeyError) as e:
        logging.error(f"Failed to parse queue message. Error: {e}", exc_info=True)
        return

    try:
        embedding_service = EmbeddingService()
        scraped_pages_service = ScrapedPagesService()
        
        embedding_service.process_and_embed_text(scraped_page_id, user_id, page_text_content, task_id, url)
        scraped_pages_service.update_scraped_page_status(task_id, url, "Completed")
        logging.info(f"Successfully processed and embedded {url}.")
    except Exception as e:
        scraped_pages_service = ScrapedPagesService()
        scraped_pages_service.update_scraped_page_status(task_id, url, "Failed")
        logging.error(f"Failed to process and embed {url}. Error: {e}", exc_info=True)
