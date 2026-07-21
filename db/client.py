"""Supabase client access. The ONLY place that imports the Supabase SDK.

Session isolation
-----------------
This module used to hand out ONE process-wide client and log users into it.
Because the app is a single server process serving every user, that meant the
client's auth session was global: whoever signed in most recently owned it, so
get_current_user() returned that person for *everyone*. Signing in as a student
would flip an admin's session to student and vice versa, and RLS-protected
queries ran as the wrong identity.

Now the caller's access token lives in a contextvar (per-task, so concurrent
requests can't clobber each other) and get_client() returns a client bound to
that token via an Authorization header. Nothing mutates shared auth state.
"""

import contextvars
from collections import OrderedDict

from supabase import create_client, Client, ClientOptions
import config

# Unauthenticated client -- safe to share, it carries no per-user auth state.
_anon_client: Client | None = None
# service_role client -- bypasses RLS. Also stateless w.r.t. user sessions.
_service_client: Client | None = None

# Access token for the request currently being handled. ContextVar (not a
# plain global) so concurrent async event handlers each see their own value.
_access_token: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "etude_access_token", default=None
)

# Building a client does TLS/session setup, so reuse per token. Bounded so a
# long-lived process can't accumulate one entry per login forever.
_MAX_CACHED_CLIENTS = 64
_client_cache: "OrderedDict[str, Client]" = OrderedDict()


def set_access_token(token: str | None) -> None:
    """Bind the current context to a user's access token.

    Call this before touching the DB on behalf of a signed-in user. Passing
    None returns the context to anonymous.
    """
    _access_token.set(token)


def get_access_token() -> str | None:
    return _access_token.get()


def clear_access_token() -> None:
    _access_token.set(None)


def _require_config() -> None:
    if not config.SUPABASE_URL or not config.SUPABASE_KEY:
        raise ValueError("SUPABASE_URL or SUPABASE_KEY not set in .env")


def _anon() -> Client:
    global _anon_client
    _require_config()
    if _anon_client is None:
        _anon_client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
    return _anon_client


def _for_token(token: str) -> Client:
    """A client whose PostgREST/Storage calls run as the token's user."""
    _require_config()

    cached = _client_cache.get(token)
    if cached is not None:
        _client_cache.move_to_end(token)
        return cached

    client = create_client(
        config.SUPABASE_URL,
        config.SUPABASE_KEY,
        options=ClientOptions(headers={"Authorization": f"Bearer {token}"}),
    )

    _client_cache[token] = client
    while len(_client_cache) > _MAX_CACHED_CLIENTS:
        _client_cache.popitem(last=False)

    return client


def get_client() -> Client:
    """Client for the current context.

    Bound to the signed-in user's token when one is set (see
    set_access_token), otherwise anonymous. Never carries another user's
    identity.
    """
    token = _access_token.get()
    return _for_token(token) if token else _anon()


def get_anon_client() -> Client:
    """Explicitly unauthenticated client, for pre-login calls."""
    return _anon()


def get_service_client() -> Client:
    """service_role client. Bypasses RLS entirely -- never expose this, or the
    key it wraps, to a browser. Server-only, for operations that must run
    before a user has a session (e.g. the SRN->email lookup during login)."""
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
