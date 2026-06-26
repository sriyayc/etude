"""Repository for users table operations."""

from db.client import get_client

client = get_client()


def get_user(user_id: str):
    response = (
        client.table("users")
        .select("*")
        .eq("id", user_id)
        .single()
        .execute()
    )

    return response.data


def get_user_by_email(email: str):
    response = (
        client.table("users")
        .select("*")
        .eq("email", email)
        .single()
        .execute()
    )

    return response.data


def create_user(
    user_id: str,
    email: str,
    full_name: str,
    role: str,
):
    response = (
        client.table("users")
        .insert(
            {
                "id": user_id,
                "email": email,
                "full_name": full_name,
                "role": role,
            }
        )
        .execute()
    )

    return response.data


def update_role(user_id: str, role: str):
    response = (
        client.table("users")
        .update({"role": role})
        .eq("id", user_id)
        .execute()
    )

    return response.data


def get_role(user_id: str):
    response = (
        client.table("users")
        .select("role")
        .eq("id", user_id)
        .single()
        .execute()
    )

    return response.data["role"]



