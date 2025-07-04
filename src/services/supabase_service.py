import os
from supabase import create_client, Client
import logging

def get_supabase_client() -> Client:
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        logging.error(f"Error creating Supabase client: {e}")
        raise # Re-raise the exception after logging
