"""Supabase provider."""

from supabase import create_client, Client
import config


if not config.SUPABASE_URL:
    raise ValueError("SUPABASE_URL not set")

if not config.SUPABASE_KEY:
    raise ValueError("SUPABASE_KEY not set")


supabase: Client = create_client(
    config.SUPABASE_URL,
    config.SUPABASE_KEY,
)


def get_client() -> Client:
    return supabase