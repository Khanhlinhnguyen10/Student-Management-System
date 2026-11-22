
"""Real SQL Server Authentication integration check.

Run from backend/: python check_auth_http_local.py

Use a development test account only. This script creates
a UserSessions record and revokes it during Logout.
"""

import getpass
import sys

from app import create_app


def main() -> int:
    print(
        "=== Group 05: REAL Login / Me / CSRF / Logout integration ==="
    )

    username = input(
        "Test username: "
    ).strip()

    role = input(
        "Role [student/lecturer/admin]: "
    ).strip().lower()

    password = getpass.getpass(
        "Test password (hidden): "
    )

    if (
        not username
        or role not in {
            "student",
            "lecturer",
            "admin",
        }
        or not password
    ):
        print(
            "Invalid test credentials/role input."
        )
        return 1

    app = create_app()
    origin = app.config["AUTH_ALLOWED_ORIGIN"]
    client = app.test_client()

    response = client.post(
        "/api/auth/login",
        json={
            "username": username,
            "password": password,
            "role": role,
        },
        headers={
            "Origin": origin,
        },
    )

    password = None

    print("Login:", response.status_code)

    if response.status_code != 200:
        print(
            "Login was not confirmed; "
            "inspect the account, role, and DB logs."
        )
        return 1

    user = response.json.get("user", {})

    print(
        "Authenticated role:",
        user.get("role"),
    )

    response = client.get(
        "/api/auth/me"
    )

    print(
        "Session verification:",
        response.status_code,
    )

    if response.status_code != 200:
        print(
            "Session lookup failed after login; "
            "inspect Stored Procedures."
        )
        return 1

    response = client.get(
        "/api/auth/csrf"
    )

    print(
        "CSRF token retrieval:",
        response.status_code,
    )

    if response.status_code != 200:
        return 1

    csrf_token = response.json[
        "csrfToken"
    ]

    response = client.post(
        "/api/auth/logout",
        headers={
            "Origin": origin,
            "X-CSRF-Token": csrf_token,
        },
    )

    print(
        "Logout (SQL revocation):",
        response.status_code,
    )

    if response.status_code != 200:
        return 1

    response = client.get(
        "/api/auth/me"
    )

    print(
        "Session access after logout:",
        response.status_code,
    )

    if response.status_code != 401:
        return 1

    print(
        "SUCCESS: real SQL-backed Login, "
        "Session and Logout verified."
    )

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())

    except KeyboardInterrupt:
        print(
            "\nIntegration check interrupted."
        )
        sys.exit(130)
