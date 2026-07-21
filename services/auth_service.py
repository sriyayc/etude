"""Authentication service."""

from db.client import (
    get_client,
    get_anon_client,
    get_service_client,
    set_access_token,
    clear_access_token,
)
from db import users_repo


def srn_is_available(srn: str) -> bool:
    """Pre-flight check so a taken SRN gives a real message.

    users.srn is UNIQUE, so otherwise the profile trigger raises
    unique_violation, which aborts the auth insert and surfaces as an opaque
    "Database error saving new user".
    """
    response = get_client().rpc(
        "srn_available", {"p_srn": srn}
    ).execute()
    return bool(response.data)


def signup_student(
    email: str,
    password: str,
    full_name: str,
    srn: str,
) -> dict:
    """Create a student account against the user's *personal* email.

    The profile row is NOT inserted here -- the on_auth_user_created trigger
    creates it from user_metadata. Doing it client-side breaks the moment
    email confirmation is enabled, because sign_up() then returns no session
    and the RLS insert (auth.uid() = id) is rejected.
    """
    srn = srn.strip().upper()
    email = email.strip().lower()

    if not srn_is_available(srn):
        raise ValueError(f"{srn} is already registered. Try signing in instead.")

    client = get_client()
    response = client.auth.sign_up({
        "email": email,
        "password": password,
        # Read by handle_new_user(). 'role' is deliberately NOT passed --
        # the trigger hard-codes 'student' so metadata can't grant admin.
        "options": {"data": {"full_name": full_name.strip(), "srn": srn}},
    })

    if response.user is None:
        raise Exception("Signup failed")

    return {
        "user_id": response.user.id,
        "email":   email,
        "role":    "student",
        "srn":     srn,
        # False when Supabase is set to require email confirmation.
        "needs_confirmation": response.session is None,
    }


def request_password_reset(email: str, redirect_to: str | None = None) -> None:
    """Send a password-reset email.

    Always returns without error even for unknown addresses -- reporting
    "no such account" here would let anyone enumerate registered emails.
    """
    try:
        get_client().auth.reset_password_for_email(
            email.strip().lower(),
            {"redirect_to": redirect_to} if redirect_to else {},
        )
    except Exception:
        pass


def update_password(new_password: str) -> None:
    """Set a new password for the currently-authenticated recovery session."""
    get_client().auth.update_user({"password": new_password})


def signup_admin(
    email: str,
    password: str,
    full_name: str,
    invite_token: str,
) -> dict:
    """
    Signs up as a student first (the only role RLS allows self-serve
    INSERT to set), then promotes via the promote_to_admin RPC, which
    checks invite_token against the private app_secrets table in the
    database -- never against app-layer config. If the token is wrong,
    the promotion is rejected and the account is left as a student.
    """
    client = get_client()
    response = client.auth.sign_up({
        "email": email,
        "password": password,
        "options": {"data": {"role": "student"}}
    })

    if response.user is None:
        raise Exception("Signup failed")

    # Profile row comes from the on_auth_user_created trigger.
    #
    # promote_to_admin() reads auth.uid(), so it needs a live session. With
    # email confirmation enabled sign_up() returns none, and promotion has to
    # happen after the user confirms and signs in.
    if response.session is None:
        raise Exception(
            "Confirm your email, sign in, then run the admin promotion. "
            "The account was created as a student."
        )

    try:
        client.rpc(
            "promote_to_admin", {"p_invite_token": invite_token}
        ).execute()
    except Exception:
        raise PermissionError("Invalid admin invite token")

    return {
        "user_id": response.user.id,
        "email":   email,
        "role":    "admin",
    }


def login(srn: str, password: str) -> dict:
    """
    Login by SRN. Uses a Supabase RPC function to look up the email
    from the SRN (direct table read blocked by RLS before auth),
    then authenticates with Supabase Auth.
    """
    # get_email_by_srn is only granted to service_role (SRNs are
    # sequential/enumerable, so it must never be reachable with the public
    # anon key) -- use the service client here, not the user-facing one.
    email_response = get_service_client().rpc(
        "get_email_by_srn", {"p_srn": srn}
    ).execute()
    email = email_response.data

    if not email:
        raise Exception("No account found for that SRN")

    # Sign in on a throwaway ANON client. Signing in on a shared client would
    # store this user's session on it and hand that identity to every other
    # user of the process -- that is what made admins and students swap roles.
    response = get_anon_client().auth.sign_in_with_password({
        "email": email,
        "password": password,
    })

    if response.user is None or response.session is None:
        raise Exception("Invalid SRN or password")

    # Bind this context to the new token so the profile read below (and the
    # rest of this request) runs as this user under RLS.
    set_access_token(response.session.access_token)

    profile = users_repo.get_user(response.user.id)
    if not profile:
        raise Exception(
            "Your account exists but has no profile yet. Contact an admin."
        )

    return {
        "user_id":       response.user.id,
        "email":         response.user.email,
        "srn":           profile["srn"],
        "full_name":     profile["full_name"],
        "role":          profile["role"],
        "access_token":  response.session.access_token,
        "refresh_token": response.session.refresh_token,
        # kept for backwards compatibility with existing callers
        "session_token": response.session.access_token,
    }


def logout() -> None:
    """Drop this context's identity.

    Deliberately does NOT call auth.sign_out() on a shared client -- that
    would revoke/replace state other users' requests depend on.
    """
    clear_access_token()


def get_current_user() -> dict:
    """Resolve the identity of the *current context* only.

    Reads the bound access token explicitly rather than whatever session a
    shared client happens to be holding.
    """
    from db.client import get_access_token

    token = get_access_token()
    if not token:
        raise Exception("User not authenticated")

    # Validate the token itself instead of trusting ambient client state.
    # get_user() returns None (not just a None .user) for an expired or
    # malformed token, so guard the response itself before touching .user.
    try:
        response = get_anon_client().auth.get_user(token)
    except Exception:
        raise Exception("User not authenticated")

    if response is None or response.user is None:
        raise Exception("User not authenticated")

    profile = users_repo.get_user(response.user.id)
    if not profile:
        raise Exception("User not authenticated")

    return {
        "user_id":   response.user.id,
        "email":     response.user.email,
        "role":      profile["role"],
        "full_name": profile.get("full_name"),
        "srn":       profile.get("srn"),
    }


def require_admin() -> dict:
    user = get_current_user()
    if user["role"] != "admin":
        raise PermissionError("Admin access required")
    return user
