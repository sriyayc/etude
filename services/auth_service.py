"""Authentication service."""

from db.client import get_client, get_service_client
from db import users_repo


def signup_student(
    email: str,
    password: str,
    full_name: str,
    srn: str,
) -> dict:
    client = get_client()
    response = client.auth.sign_up({
        "email": email,
        "password": password,
        "options": {"data": {"role": "student"}}
    })

    if response.user is None:
        raise Exception("Signup failed")

    users_repo.create_user(
        user_id=response.user.id,
        email=email,
        full_name=full_name,
        role="student",
        srn=srn,
    )

    return {
        "user_id": response.user.id,
        "email":   email,
        "role":    "student",
        "srn":     srn,
    }


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

    users_repo.create_user(
        user_id=response.user.id,
        email=email,
        full_name=full_name,
        role="student",
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
    client = get_client()

    # get_email_by_srn is only granted to service_role (SRNs are
    # sequential/enumerable, so it must never be reachable with the public
    # anon key) -- use the service client here, not the user-facing one.
    email_response = get_service_client().rpc(
        "get_email_by_srn", {"p_srn": srn}
    ).execute()
    email = email_response.data

    if not email:
        raise Exception("No account found for that SRN")

    response = client.auth.sign_in_with_password({
        "email": email,
        "password": password,
    })

    if response.user is None or response.session is None:
        raise Exception("Invalid SRN or password")

    profile = users_repo.get_user(response.user.id)

    return {
        "user_id":       response.user.id,
        "email":         response.user.email,
        "srn":           profile["srn"],
        "full_name":     profile["full_name"],
        "role":          profile["role"],
        "session_token": response.session.access_token,
    }


def logout() -> None:
    get_client().auth.sign_out()


def get_current_user() -> dict:
    client = get_client()
    response = client.auth.get_user()

    if response.user is None:
        raise Exception("User not authenticated")

    profile = users_repo.get_user(response.user.id)

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
