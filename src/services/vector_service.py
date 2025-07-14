import logging
from typing import Optional
from src.services.supabase_service import get_supabase_service_role_client

class VectorService:
    """
    A service class for managing vector embeddings in Supabase.
    """

    def __init__(self):
        self.supabase_service_role = get_supabase_service_role_client()

    def insert_text_chunk_with_embedding(self, scraped_page_id: int, user_id: str, chunk_text: str, embedding: list) -> Optional[int]:
        """
        Inserts a text chunk and its embedding into the 'page_chunks' table.
        """
        try:
            data_to_insert = {
                "scraped_page_id": scraped_page_id,
                "user_id": user_id,
                "chunk_text": chunk_text,
                "embedding": embedding,
            }
            response = self.supabase_service_role.table('page_chunks').insert(data_to_insert).execute()
            if response.data:
                chunk_id = response.data[0]['id']
                logging.info(f"Inserted text chunk for scraped_page_id {scraped_page_id}, user_id {user_id} with chunk_id {chunk_id}.")
                return chunk_id
            else:
                logging.error(f"Failed to insert text chunk for scraped_page_id {scraped_page_id}, user_id {user_id}: {response.status_code} - {response.text}", exc_info=True)
                return None
        except Exception as e:
            logging.error(f"Error inserting text chunk for scraped_page_id {scraped_page_id}, user_id {user_id}: {e}", exc_info=True)
            return None
