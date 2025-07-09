import os
# from supabase import create_client, Client
import logging

def get_supabase_client() :
    """
    Initializes and returns a Supabase client using the standard Supabase key.

    Retrieves Supabase URL and Key from environment variables.

    Returns:
        Client: An initialized Supabase client instance.

    Raises:
        Exception: If there is an error creating the Supabase client.
    """
    return None
    # SUPABASE_URL = os.environ.get("SUPABASE_URL")
    # SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
    # try:
    #     client = create_client(SUPABASE_URL, SUPABASE_KEY)
    #     return client
    # except Exception as e:
    #     logging.error(f"Error creating Supabase client: {e}", exc_info=True)
    #     raise # Re-raise the exception after logging

def get_supabase_service_role_client() :
    """
    Initializes and returns a Supabase client using the service role key.
    This client bypasses Row Level Security (RLS) and should be used for
    server-side operations that require elevated privileges (e.g., inserts, updates, deletes
    that might be blocked by RLS for anonymous users).

    Retrieves Supabase URL and SERVICE_ROLE_KEY from environment variables.

    Returns:
        Client: An initialized Supabase client instance with service role privileges.

    Raises:
        Exception: If there is an error creating the Supabase service role client.
    """
    return None


    # SUPABASE_URL = os.environ.get("SUPABASE_URL")
    # SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    # try:
    #     return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    # except Exception as e:
    #     logging.error(f"Error creating Supabase service role client: {e}", exc_info=True)
    #     raise # Re-raise the exception after logging
