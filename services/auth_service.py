"""Authentication service."""

import config

from db.client import get_client
from db import users_repo

client = get_client()


def signup_student(
    email: str,
    password: str,
    full_name: str,
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
    )

    return {
        "user_id": response.user.id,
        "email": email,
        "role": "student",
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




def login(email: str, password: str) -> dict:
    """
    Login a user and return session information.
    """

    response = client.auth.sign_in_with_password(
        {
            "email": email,
            "password": password,
        }
    )

    if response.user is None or response.session is None:
        raise Exception("Invalid email or password")

    role = users_repo.get_role(response.user.id)

    return {
        "user_id": response.user.id,
        "email": response.user.email,
        "role": role,
        "session_token": response.session.access_token,
    }


def logout() -> None:
    """
    Logout the current user.
    """

    client.auth.sign_out()



def get_current_user() -> dict:
    """
    Return the currently authenticated user.
    """

    response = client.auth.get_user()

    if response.user is None:
        raise Exception("User not authenticated")

    role = users_repo.get_role(response.user.id)

    return {
        "user_id": response.user.id,
        "email": response.user.email,
        "role": role,
    }




def require_teacher() -> dict:
    """
    Ensure the current user is a teacher.
    """

    user = get_current_user()

    if user["role"] != "teacher":
        raise PermissionError("Teacher access required")

    return user





