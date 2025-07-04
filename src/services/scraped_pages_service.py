import logging
from src.services.supabase_service import get_supabase_client

supabase = get_supabase_client()

def insert_scraped_page(task_id: str, url: str, status: str) -> int | None:
    """
    Inserts a new scraped page entry into the 'scraped_pages' table,
    or logs if the entry already exists for the given task_id and URL.
    Returns the ID of the inserted/existing page, or None on error.
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
                logging.error(f"Failed to insert scraped page: {insert_response.status_code} - {insert_response.text}")
                return None
        else:
            logging.info(f"Scraped page already exists: Task ID: {task_id}, URL: {url}. Skipping insert.")
            return response.data[0]['id']
    except Exception as e:
        logging.error(f"Error inserting scraped page (Task ID: {task_id}, URL: {url}): {e}")
        return None

def update_scraped_page_status(task_id: str, url: str, status: str, page_text_content: str = None) -> bool:
    """
    Updates the status and optionally adds html_content and page_text_content
    of an existing scraped page entry in the 'scraped_pages' table.
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
        logging.error(f"Error updating scraped page (Task ID: {task_id}, URL: {url}): {e}")
        return False

def insert_text_chunk_with_embedding(scraped_page_id: int, chunk_text: str, embedding: list) -> bool:
    """
    Inserts a text chunk and its embedding into the 'page_chunks' table.
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
            logging.error(f"Failed to insert text chunk for scraped_page_id {scraped_page_id}: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logging.error(f"Error inserting text chunk for scraped_page_id {scraped_page_id}: {e}")
        return False
