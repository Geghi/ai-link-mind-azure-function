import os
from supabase import create_client, Client

def get_supabase_client() -> Client:
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
    return create_client(SUPABASE_URL, SUPABASE_KEY)
