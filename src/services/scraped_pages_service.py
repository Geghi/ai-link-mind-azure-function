import logging
from src.services.supabase_service import get_supabase_client, get_supabase_service_role_client

supabase = get_supabase_client()
supabase_service_role = get_supabase_service_role_client()


def get_scraped_urls_for_task(task_id: str, user_id: str) -> set[str]:
    """
    Retrieves all URLs already scraped or queued for a given task_id.
    Uses the service role client to bypass RLS for internal checks.

    Args:
        task_id (str): The ID of the scraping task.

    Returns:
        set[str]: A set of URLs associated with the task.
    """
    try:
        # Use supabase_service_role to bypass RLS for this internal check
        response = supabase_service_role.table('scraped_pages').select('url').eq('task_id', task_id).eq("user_id", user_id).execute()
        if response.data:
            return {record['url'] for record in response.data}
        return set()
    except Exception as e:
        logging.error(f"Error retrieving scraped URLs for task {task_id}: {e}", exc_info=True)
        return set()

def insert_scraped_page(task_id: str, user_id: str, url: str, status: str) -> int | None:
    """
    Inserts a new scraped page entry if it doesn't already exist.
    Uses the service role client to bypass RLS for initial data creation.

    Args:
        task_id (str): The ID of the scraping task.
        user_id (str): The ID of the user associated with the task.
        url (str): The URL of the page that was scraped.
        status (str): The initial status of the scraped page (e.g., "Queued").

    Returns:
        int | None: The ID of the newly inserted page, or None if the page already existed or an error occurred.
    """
    try:
        data_to_upsert = {"task_id": task_id, "user_id": user_id, "url": url, "status": status}
        
        # Use upsert with ignore_duplicates=True.
        # This will only insert a new record if the combination of task_id and url does not already exist.
        # If the record is a duplicate, it will be ignored, and the response will be empty.
        upsert_response = supabase_service_role.table('scraped_pages').upsert(
            data_to_upsert, 
            on_conflict='task_id,url', 
            ignore_duplicates=True
        ).execute()
        
        if upsert_response.data:
            logging.info(f"Inserted new scraped page: Task ID: {task_id}, User ID: {user_id}, URL: {url}, Status: {status}")
            return upsert_response.data[0]['id']
        else:
            # This can mean the record already existed (and was ignored) or an error occurred.
            # The log below will capture the error case. If no error, it was a duplicate.
            logging.info(f"Scraped page already exists or failed to insert: Task ID: {task_id}, URL: {url}")
            return None
    except Exception as e:
        logging.error(f"Error upserting scraped page (Task ID: {task_id}, User ID: {user_id}, URL: {url}): {e}", exc_info=True) # Update log
        return None

def update_scraped_page_status(task_id: str, url: str, status: str, page_text_content: str = None) -> bool:
    """
    Updates the status and optionally the text content of an existing scraped page entry
    in the 'scraped_pages' table. Uses the service role client to bypass RLS.

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

        response = supabase_service_role.table('scraped_pages').update(data_to_update).eq('task_id', task_id).eq('url', url).execute()
        if response.data:
            logging.info(f"Updated scraped page: Task ID: {task_id}, URL: {url}, Status: {status}")
            return True
        else:
            logging.info(f"Scraped page not found for update: Task ID: {task_id}, URL: {url}")
            return False
    except Exception as e:
        logging.error(f"Error updating scraped page (Task ID: {task_id}, URL: {url}): {e}", exc_info=True)
        return False

def insert_text_chunk_with_embedding(scraped_page_id: int, user_id: str, chunk_text: str, embedding: list) -> int | None:
    """
    Inserts a text chunk and its embedding into the 'page_chunks' table.
    Uses the service role client to bypass RLS.

    Args:
        scraped_page_id (int): The foreign key linking to the 'scraped_pages' table.
        user_id (str): The ID of the user associated with the chunk.
        chunk_text (str): The text content of the chunk.
        embedding (list): The OpenAI embedding for the text chunk.

    Returns:
        int | None: The ID of the inserted chunk, or None if an error occurs.
    """
    try:
        data_to_insert = {
            "scraped_page_id": scraped_page_id,
            "user_id": user_id,
            "chunk_text": chunk_text,
            "embedding": embedding,
        }
        response = supabase_service_role.table('page_chunks').insert(data_to_insert).execute()
        if response.data:
            chunk_id = response.data[0]['id']
            logging.info(f"Inserted text chunk for scraped_page_id {scraped_page_id}, user_id {user_id} with chunk_id {chunk_id}.") # Update log
            return chunk_id
        else:
            logging.error(f"Failed to insert text chunk for scraped_page_id {scraped_page_id}, user_id {user_id}: {response.status_code} - {response.text}", exc_info=True) # Update log
            return None
    except Exception as e:
        logging.error(f"Error inserting text chunk for scraped_page_id {scraped_page_id}, user_id {user_id}: {e}", exc_info=True) # Update log
        return None
