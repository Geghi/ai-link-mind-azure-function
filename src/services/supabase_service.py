import os
from supabase import create_client, Client
import logging

def get_supabase_client() -> Client:
    """
    Initializes and returns a Supabase client.

    Retrieves Supabase URL and Key from environment variables.

    Returns:
        Client: An initialized Supabase client instance.

    Raises:
        Exception: If there is an error creating the Supabase client.
    """
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        logging.error(f"Error creating Supabase client: {e}", exc_info=True)
        raise # Re-raise the exception after logging
