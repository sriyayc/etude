"""
Regression test for the users.role authorization model.

Exercises the exact attack sequence used to verify the fix live against
Supabase (see db/schema.sql, db/hardening_patch.sql): a signed-up-but-
otherwise-normal student must not be able to reach role='admin' through
any path except promote_to_admin() with the correct invite token.

Hits the live Supabase project directly over its REST API -- the same
thing an attacker holding only the public anon key would do. Creates one
throwaway auth user per run and deletes it in a finally block regardless
of outcome.

Run directly: python tests/test_authz.py
"""

import os
import sys
import uuid

import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config

REST_URL = f"{config.SUPABASE_URL}/rest/v1"
AUTH_URL = f"{config.SUPABASE_URL}/auth/v1"


def _signup_throwaway_student() -> tuple[str, str]:
    email = f"authz-test-{uuid.uuid4().hex[:12]}@example.com"
    password = f"Test-{uuid.uuid4().hex}Aa1!"

    resp = requests.post(
        f"{AUTH_URL}/signup",
        headers={"apikey": config.SUPABASE_KEY, "Content-Type": "application/json"},
        json={"email": email, "password": password},
    )
    resp.raise_for_status()
    body = resp.json()
    return body["user"]["id"], body["access_token"], email


def _delete_user(user_id: str) -> None:
    requests.delete(
        f"{AUTH_URL}/admin/users/{user_id}",
        headers={
            "apikey": config.SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {config.SUPABASE_SERVICE_ROLE_KEY}",
        },
    )


def _student_headers(jwt: str) -> dict:
    return {
        "apikey": config.SUPABASE_KEY,
        "Authorization": f"Bearer {jwt}",
        "Content-Type": "application/json",
    }


def test_cannot_insert_self_as_admin(uid: str, jwt: str, email: str) -> None:
    resp = requests.post(
        f"{REST_URL}/users",
        headers=_student_headers(jwt),
        json={"id": uid, "email": email, "full_name": "x", "role": "admin"},
    )
    assert resp.status_code >= 400, (
        f"direct INSERT with role=admin should be rejected by RLS, "
        f"got {resp.status_code}: {resp.text}"
    )


def test_cannot_patch_role_to_admin(uid: str, jwt: str, email: str) -> None:
    # Needs an existing row -- legit self-insert as student first.
    resp = requests.post(
        f"{REST_URL}/users",
        headers=_student_headers(jwt),
        json={"id": uid, "email": email, "full_name": "x", "role": "student"},
    )
    assert resp.status_code < 300, f"legit student self-insert failed: {resp.text}"

    resp = requests.patch(
        f"{REST_URL}/users?id=eq.{uid}",
        headers=_student_headers(jwt),
        json={"role": "admin"},
    )
    assert resp.status_code >= 400, (
        f"PATCH role=admin should be rejected by the role-freeze trigger, "
        f"got {resp.status_code}: {resp.text}"
    )

    resp = requests.get(
        f"{REST_URL}/users?id=eq.{uid}&select=role", headers=_student_headers(jwt)
    )
    assert resp.json()[0]["role"] == "student", "role changed despite rejected PATCH"


def test_legit_profile_edit_still_works(uid: str, jwt: str) -> None:
    resp = requests.patch(
        f"{REST_URL}/users?id=eq.{uid}",
        headers=_student_headers(jwt),
        json={"full_name": "Renamed"},
    )
    assert resp.status_code < 300, (
        f"non-role profile edit should be allowed, got "
        f"{resp.status_code}: {resp.text}"
    )


def test_promote_to_admin_rejects_wrong_token(uid: str, jwt: str) -> None:
    resp = requests.post(
        f"{REST_URL}/rpc/promote_to_admin",
        headers=_student_headers(jwt),
        json={"p_invite_token": "wrong"},
    )
    assert resp.status_code >= 400, (
        f"promote_to_admin with a wrong token should be rejected, got "
        f"{resp.status_code}: {resp.text}"
    )

    resp = requests.get(
        f"{REST_URL}/users?id=eq.{uid}&select=role", headers=_student_headers(jwt)
    )
    assert resp.json()[0]["role"] == "student", "role changed despite wrong token"


def test_get_email_by_srn_blocked_for_anon() -> None:
    resp = requests.post(
        f"{REST_URL}/rpc/get_email_by_srn",
        headers={"apikey": config.SUPABASE_KEY, "Content-Type": "application/json"},
        json={"p_srn": "PES1UG23CS0001"},
    )
    assert resp.status_code >= 400, (
        f"get_email_by_srn must not be callable with the public anon key, "
        f"got {resp.status_code}: {resp.text}"
    )


def main() -> None:
    uid, jwt, email = _signup_throwaway_student()
    tests = [
        ("cannot INSERT self as admin", lambda: test_cannot_insert_self_as_admin(uid, jwt, email)),
        ("cannot PATCH role to admin", lambda: test_cannot_patch_role_to_admin(uid, jwt, email)),
        ("legit profile edit still works", lambda: test_legit_profile_edit_still_works(uid, jwt)),
        ("promote_to_admin rejects wrong token", lambda: test_promote_to_admin_rejects_wrong_token(uid, jwt)),
        ("get_email_by_srn blocked for anon", test_get_email_by_srn_blocked_for_anon),
    ]

    failures = []
    try:
        for name, fn in tests:
            try:
                fn()
                print(f"PASS: {name}")
            except AssertionError as e:
                print(f"FAIL: {name} -- {e}")
                failures.append(name)
    finally:
        _delete_user(uid)

    if failures:
        print(f"\n{len(failures)}/{len(tests)} FAILED: {', '.join(failures)}")
        sys.exit(1)
    print(f"\nAll {len(tests)} authz tests passed.")


if __name__ == "__main__":
    main()
