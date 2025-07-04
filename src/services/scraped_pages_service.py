import logging
from src.services.supabase_service import get_supabase_client

supabase = get_supabase_client()

def insert_scraped_page(task_id: str, url: str, status: str) -> int | None:
    """
    Inserts a new scraped page entry into the 'scraped_pages' table.
    If an entry with the given task_id and URL already exists, it logs a message
    and returns the ID of the existing entry.

    Args:
        task_id (str): The ID of the scraping task.
        url (str): The URL of the page that was scraped.
        status (str): The initial status of the scraped page (e.g., "Queued", "Processing").

    Returns:
        int | None: The ID of the inserted or existing scraped page, or None if an error occurs.
    """
    try:
        # Check if the link already exists for this task_id and URL
        response = supabase.table('scraped_pages').select('id, url').eq('task_id', task_id).eq('url', url).execute()
        
        if not response.data: # If link does not exist, insert
            insert_response = supabase.table('scraped_pages').insert({"task_id": task_id, "url": url, "status": status}).execute()
            if insert_response.data:
                logging.info(f"Inserted new scraped page: Task ID: {task_id}, URL: {url}, Status: {status}")
                return insert_response.data[0]['id']
            else:
                logging.error(f"Failed to insert scraped page: {insert_response.status_code} - {insert_response.text}", exc_info=True)
                return None
        else:
            logging.info(f"Scraped page already exists: Task ID: {task_id}, URL: {url}. Skipping insert.")
            return response.data[0]['id']
    except Exception as e:
        logging.error(f"Error inserting scraped page (Task ID: {task_id}, URL: {url}): {e}", exc_info=True)
        return None

def update_scraped_page_status(task_id: str, url: str, status: str, page_text_content: str = None) -> bool:
    """
    Updates the status and optionally the text content of an existing scraped page entry
    in the 'scraped_pages' table.

    Args:
        task_id (str): The ID of the scraping task.
        url (str): The URL of the page to update.
        status (str): The new status of the scraped page (e.g., "Processing", "Completed", "Failed").
        page_text_content (str, optional): The extracted text content of the page. Defaults to None.

    Returns:
        bool: True if the update was successful, False otherwise.
    """
    try:
        data_to_update = {"status": status}
        if page_text_content is not None:
            data_to_update["page_text_content"] = page_text_content

        response = supabase.table('scraped_pages').update(data_to_update).eq('task_id', task_id).eq('url', url).execute()
        if response.data:
            logging.info(f"Updated scraped page: Task ID: {task_id}, URL: {url}, Status: {status}")
            return True
        else:
            logging.info(f"Scraped page not found for update: Task ID: {task_id}, URL: {url}")
            return False
    except Exception as e:
        logging.error(f"Error updating scraped page (Task ID: {task_id}, URL: {url}): {e}", exc_info=True)
        return False

def insert_text_chunk_with_embedding(scraped_page_id: int, chunk_text: str, embedding: list) -> bool:
    """
    Inserts a text chunk and its embedding into the 'page_chunks' table.

    Args:
        scraped_page_id (int): The foreign key linking to the 'scraped_pages' table.
        chunk_text (str): The text content of the chunk.
        embedding (list): The OpenAI embedding for the text chunk.

    Returns:
        bool: True if the insertion was successful, False otherwise.
    """
    try:
        data_to_insert = {
            "scraped_page_id": scraped_page_id,
            "chunk_text": chunk_text,
            "embedding": embedding,
        }
        response = supabase.table('page_chunks').insert(data_to_insert).execute()
        if response.data:
            logging.info(f"Inserted text chunk for scraped_page_id {scraped_page_id}.")
            return True
        else:
            logging.error(f"Failed to insert text chunk for scraped_page_id {scraped_page_id}: {response.status_code} - {response.text}", exc_info=True)
            return False
    except Exception as e:
        logging.error(f"Error inserting text chunk for scraped_page_id {scraped_page_id}: {e}", exc_info=True)
        return False
