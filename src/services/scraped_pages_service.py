import logging
from src.services.supabase_service import get_supabase_client

supabase = get_supabase_client()

def insert_scraped_page(task_id: str, url: str, status: str):
    """
    Inserts a new scraped page entry into the 'scraped_pages' table,
    or logs if the entry already exists for the given task_id and URL.
    """
    try:
        # Check if the link already exists for this task_id and URL
        response = supabase.table('scraped_pages').select('url').eq('task_id', task_id).eq('url', url).execute()
        
        if not response.data: # If link does not exist, insert
            supabase.table('scraped_pages').insert({"task_id": task_id, "url": url, "status": status}).execute()
            logging.info(f"Inserted new scraped page: Task ID: {task_id}, URL: {url}, Status: {status}")
            return True
        else:
            logging.info(f"Scraped page already exists: Task ID: {task_id}, URL: {url}. Skipping insert.")
            return False
    except Exception as e:
        logging.error(f"Error inserting scraped page (Task ID: {task_id}, URL: {url}): {e}")
        return False
