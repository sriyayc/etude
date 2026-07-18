"""Supabase client singleton. The ONLY place that imports the Supabase SDK."""

from supabase import create_client, Client
import config

_client: Client = None
_service_client: Client = None


def get_client() -> Client:
    """Lazy-initialized singleton using the public anon/publishable key.
    Subject to RLS -- use this for anything acting on behalf of a signed-in
    (or signing-up) user."""
    global _client
    if _client is None:
        if not config.SUPABASE_URL or not config.SUPABASE_KEY:
            raise ValueError("SUPABASE_URL or SUPABASE_KEY not set in .env")
        _client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
    return _client


def get_service_client() -> Client:
    """Lazy-initialized singleton using the service_role key. Bypasses RLS
    entirely -- never expose this client, or the key it wraps, to a browser
    or any other untrusted caller. Reserve it for server-only operations
    that must run before a user has a session, like the SRN lookup in
    services/auth_service.login()."""
    global _service_client
    if _service_client is None:
        if not config.SUPABASE_URL or not config.SUPABASE_SERVICE_ROLE_KEY:
            raise ValueError(
                "SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set in .env"
            )
        _service_client = create_client(
            config.SUPABASE_URL, config.SUPABASE_SERVICE_ROLE_KEY
        )
    return _service_client