
"""Read-only SQL Server smoke test for the Login account/role lookup.

Run from backend/: python check_auth_repository.py
Does NOT create sessions, request passwords, or print password hashes.
"""

import sys
import pyodbc

from app.repositories.auth_repository import AuthRepository
from app.repositories.database import DatabaseConfigurationError


def main() -> int:
    repo = AuthRepository()
    print("=== Group 05: AuthRepository READ-ONLY check ===")
    try:
        found = 0
        for username in ("admin01", "student01", "lecturer01"):
            account = repo.get_by_username(username)
            if account is None:
                print(f"{username}: not found (sample account may not be seeded)")
                continue
            found += 1
            print(
                f"{username}: roles={','.join(account.roles) or 'NONE'} "
                f"locked={account.is_locked}"
            )
            if len(account.roles) != 1:
                print("WARNING: account must have exactly one valid role.")
        print(f"Sample accounts found: {found}/3")
        print("SUCCESS: AuthRepository can read Users and role tables.")
        print("No UserSessions records were created or changed.")
        return 0
    except (pyodbc.Error, DatabaseConfigurationError, ValueError) as exc:
        print(f"AUTH REPOSITORY CHECK FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
