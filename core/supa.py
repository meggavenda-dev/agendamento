import os
from supabase import create_client, Client


def supabase_anon() -> Client:
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_ANON_KEY"]
    return create_client(url, key)


def supabase_service() -> Client:
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    return create_client(url, key)
