import logging
from typing import List, Optional, Set
from src.services.supabase_service import get_supabase_client, get_supabase_service_role_client

class ScrapedPagesService:
    """
    A service class for managing scraped pages in Supabase.
    """

    def __init__(self):
        self.supabase_service_role = get_supabase_service_role_client()

    def get_scraped_urls_for_task(self, task_id: str, user_id: str) -> Set[str]:
        """
        Retrieves all URLs already scraped or queued for a given task_id.
        """
        try:
            response = self.supabase_service_role.table('scraped_pages').select('url').eq('task_id', task_id).eq("user_id", user_id).execute()
            if response.data:
                return {record['url'] for record in response.data}
            return set()
        except Exception as e:
            logging.error(f"Error retrieving scraped URLs for task {task_id}: {e}", exc_info=True)
            return set()

    def insert_scraped_page(self, task_id: str, user_id: str, url: str, status: str) -> Optional[int]:
        """
        Inserts a new scraped page entry if it doesn't already exist.
        """
        try:
            data_to_upsert = {"task_id": task_id, "user_id": user_id, "url": url, "status": status}
            upsert_response = self.supabase_service_role.table('scraped_pages').upsert(
                data_to_upsert,
                on_conflict='task_id,url',
                ignore_duplicates=True
            ).execute()
            if upsert_response.data:
                logging.info(f"Inserted new scraped page: Task ID: {task_id}, User ID: {user_id}, URL: {url}, Status: {status}")
                return upsert_response.data[0]['id']
            else:
                logging.info(f"Scraped page already exists or failed to insert: Task ID: {task_id}, URL: {url}")
                return None
        except Exception as e:
            logging.error(f"Error upserting scraped page (Task ID: {task_id}, User ID: {user_id}, URL: {url}): {e}", exc_info=True)
            return None

    def update_scraped_page_status(self, task_id: str, url: str, status: str, page_text_content: Optional[str] = None) -> bool:
        """
        Updates the status and optionally the text content of an existing scraped page entry.
        """
        try:
            data_to_update = {"status": status}
            if page_text_content is not None:
                data_to_update["page_text_content"] = page_text_content

            response = self.supabase_service_role.table('scraped_pages').update(data_to_update).eq('task_id', task_id).eq('url', url).execute()
            if response.data:
                logging.info(f"Updated scraped page: Task ID: {task_id}, URL: {url}, Status: {status}")
                return True
            else:
                logging.info(f"Scraped page not found for update: Task ID: {task_id}, URL: {url}")
                return False
        except Exception as e:
            logging.error(f"Error updating scraped page (Task ID: {task_id}, URL: {url}): {e}", exc_info=True)
            return False
