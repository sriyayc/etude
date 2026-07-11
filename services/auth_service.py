"""Authentication service."""

import config

from db.client import get_client
from db import users_repo

client = get_client()


def signup_student(
    email: str,
    password: str,
    full_name: str,
    srn: str,
) -> dict:
    """
    Create a new student account.
    """

    response = client.auth.sign_up(
        {
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "role": "student"
                }
            }
        }
    )

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
        "email": email,
        "role": "student",
        "srn": srn,
    }




def signup_teacher(
    email: str,
    password: str,
    full_name: str,
    invite_token: str,
) -> dict:
    """
    Create a new teacher account.
    """

    if invite_token != config.TEACHER_INVITE_TOKEN:
        raise PermissionError("Invalid teacher invite token")

    response = client.auth.sign_up(
        {
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "role": "teacher"
                }
            }
        }
    )

    if response.user is None:
        raise Exception("Signup failed")

    users_repo.create_user(
        user_id=response.user.id,
        email=email,
        full_name=full_name,
        role="teacher",
    )

    return {
        "user_id": response.user.id,
        "email": email,
        "role": "teacher",
    }




def login(srn: str, password: str) -> dict:
    """
    Login a user by their SRN. SRN and email are stored as
    separate fields — this looks up the account's real email
    via a SECURITY DEFINER RPC function (a direct table read
    would be blocked by RLS, since the caller isn't
    authenticated yet at this point), then authenticates with
    Supabase Auth (which only knows email, not SRN).
    """

    email_response = client.rpc(
        "get_email_by_srn",
        {"p_srn": srn},
    ).execute()

    email = email_response.data

    if not email:
        raise Exception("No account found for that SRN")

    response = client.auth.sign_in_with_password(
        {
            "email": email,
            "password": password,
        }
    )

    if response.user is None or response.session is None:
        raise Exception("Invalid SRN or password")

    profile = users_repo.get_user(response.user.id)

    return {
        "user_id": response.user.id,
        "email": response.user.email,
        "srn": profile["srn"],
        "full_name": profile["full_name"],
        "role": profile["role"],
        "session_token": response.session.access_token,
    }


def logout() -> None:
    """
    Logout the current user.
    """

    client.auth.sign_out()



def get_current_user() -> dict:
    """
    Return the currently authenticated user, including profile fields
    (full_name, srn) from the users table — not just the auth record.
    """

    response = client.auth.get_user()

    if response.user is None:
        raise Exception("User not authenticated")

    profile = users_repo.get_user(response.user.id)

    return {
        "user_id": response.user.id,
        "email": response.user.email,
        "role": profile["role"],
        "full_name": profile.get("full_name"),
        "srn": profile.get("srn"),
    }




def require_teacher() -> dict:
    """
    Ensure the current user is a teacher.
    """

    user = get_current_user()

    if user["role"] != "teacher":
        raise PermissionError("Teacher access required")

    return user
