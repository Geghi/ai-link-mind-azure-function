import logging
from src.services.supabase_service import get_supabase_client
from supabase import Client, PostgrestAPIResponse

def upsert_chat_summary(task_id: str, summary_text: str) -> bool:
    """
    Inserts or updates a chat summary for a given task_id in the chat_summaries table.
    If a summary for the task_id already exists, it updates the existing one.
    Otherwise, it inserts a new one.
    """
    supabase: Client = get_supabase_client()
    try:
        # Attempt to update first (if a unique constraint was on task_id, this would be an upsert)
        # Since task_id is no longer unique, we'll always insert a new record
        # and rely on fetching the LATEST summary.
        
        # For now, we'll insert a new record. If we wanted to truly "upsert"
        # on task_id without a unique constraint, we'd need to fetch the latest
        # and then update it, or delete old ones.
        # Given the user's instruction "ALways use the last.", inserting new records
        # and fetching the latest by created_at/updated_at is the correct approach.

        response: PostgrestAPIResponse = supabase.from_('chat_summaries').insert({
            "task_id": task_id,
            "summary_text": summary_text
        }).execute()

        if response.data:
            logging.info(f"Successfully inserted new chat summary for task_id: {task_id}")
            return True
        else:
            logging.error(f"Failed to insert chat summary for task_id: {task_id}. Response: {response.data}", exc_info=True)
            return False
    except Exception as e:
        logging.error(f"Error upserting chat summary for task_id {task_id}: {e}", exc_info=True)
        return False

def get_chat_summary(task_id: str) -> str | None:
    """
    Retrieves the latest chat summary for a given task_id from the chat_summaries table.
    """
    supabase: Client = get_supabase_client()
    try:
        response: PostgrestAPIResponse = supabase.from_('chat_summaries').select("summary_text") \
            .eq("task_id", task_id) \
            .order("created_at", desc=True) \
            .limit(1) \
            .execute()

        if response.data and len(response.data) > 0:
            summary = response.data[0]['summary_text']
            logging.info(f"Successfully retrieved chat summary for task_id: {task_id}")
            return summary
        else:
            logging.info(f"No chat summary found for task_id: {task_id}")
            return None
    except Exception as e:
        logging.error(f"Error retrieving chat summary for task_id {task_id}: {e}", exc_info=True)
        return None
