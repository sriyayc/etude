"""Supabase client singleton. The ONLY place that imports the Supabase SDK."""

from supabase import create_client, Client
import config

_client: Client = None


def get_client() -> Client:
    """Lazy-initialized singleton. Created on first call, reused after."""
    global _client
    if _client is None:
        if not config.SUPABASE_URL or not config.SUPABASE_KEY:
            raise ValueError("SUPABASE_URL or SUPABASE_KEY not set in .env")
        _client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
    return _client