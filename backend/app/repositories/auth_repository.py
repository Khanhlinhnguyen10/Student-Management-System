
"""Authentication data access for the official Group 05 SQL Server schema.

Reads Users and the three role tables, and calls the existing UserSessions
stored procedures. The raw session token must NEVER reach this layer.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from app.repositories.transaction import connection_scope


@dataclass(frozen=True, slots=True)
class AuthAccount:
    """Internal query DTO, not a new UML class or SQL Server table."""

    user_id: str
    username: str
    password_hash: str = field(repr=False)
    is_locked: bool = False
    full_name: str = ""
    roles: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class StoredSession:
    user_id: str
    expires_at: datetime
    session_id: str | None = None


_ACCOUNT_SQL = """
SELECT
    u.userId, u.username, u.passwordHash, u.isLocked, u.fullName,
    CASE WHEN a.userId IS NULL THEN 0 ELSE 1 END AS isAdministrator,
    CASE WHEN s.userId IS NULL THEN 0 ELSE 1 END AS isStudent,
    CASE WHEN l.userId IS NULL THEN 0 ELSE 1 END AS isLecturer
FROM dbo.Users AS u
LEFT JOIN dbo.Administrators AS a ON a.userId = u.userId
LEFT JOIN dbo.Students AS s ON s.userId = u.userId
LEFT JOIN dbo.Lecturers AS l ON l.userId = u.userId
"""


class AuthRepository:
    """DB operations only; never verifies plaintext passwords or returns HTTP."""

    def __init__(self, connection_factory: Callable[[], Any] | None = None):
        self._connection_factory = connection_factory

    @staticmethod
    def _as_account(row: Any) -> AuthAccount:
        assigned = tuple(
            role for present, role in zip(
                (row[5], row[6], row[7]),
                ("Administrator", "Student", "Lecturer"),
            )
            if bool(present)
        )
        return AuthAccount(
            user_id=row[0],
            username=row[1],
            password_hash=row[2],
            is_locked=bool(row[3]),
            full_name=row[4],
            roles=assigned,
        )

    @staticmethod
    def _utc(value: datetime) -> datetime:
        """SQL Server DATETIME2 values are UTC but pyodbc returns naive dates."""
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def _fetch_account(self, *, field: str, value: str) -> AuthAccount | None:
        if field not in ("u.username", "u.userId"):
            raise ValueError("Unexpected account search field.")
        sql = _ACCOUNT_SQL + f"WHERE {field} = ?"

        with connection_scope(
            connection_factory=self._connection_factory
        ) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(sql, value)
                row = cursor.fetchone()
                return self._as_account(row) if row is not None else None
            finally:
                cursor.close()

    def get_by_username(self, username: str) -> AuthAccount | None:
        if not isinstance(username, str) or not 1 <= len(username) <= 50:
            raise ValueError("Invalid username.")
        return self._fetch_account(field="u.username", value=username)

    def get_by_user_id(self, user_id: str) -> AuthAccount | None:
        if not isinstance(user_id, str) or not 1 <= len(user_id) <= 12:
            raise ValueError("Invalid user ID.")
        return self._fetch_account(field="u.userId", value=user_id)

    def create_session(self, user_id: str, token_hash: str) -> StoredSession:
        """Write through the project's SQL stored procedure, then COMMIT."""
        with connection_scope(
            write=True,
            connection_factory=self._connection_factory,
        ) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "EXEC dbo.usp_CreateUserSession @UserId=?, @TokenHash=?",
                    user_id,
                    token_hash,
                )
                row = cursor.fetchone()

                if row is None or row[1] != user_id:
                    raise RuntimeError(
                        "SQL Server did not confirm session creation."
                    )

                result = StoredSession(
                    user_id=row[1],
                    expires_at=self._utc(row[2]),
                    session_id=str(row[0]),
                )
            finally:
                cursor.close()

        return result

    def touch_session(self, token_hash: str) -> StoredSession | None:
        """Refresh inactivity timeout; expired/invalid session returns None."""
        with connection_scope(
            write=True,
            connection_factory=self._connection_factory,
        ) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "EXEC dbo.usp_TouchUserSession @TokenHash=?",
                    token_hash,
                )
                row = cursor.fetchone()

                result = (
                    StoredSession(
                        user_id=row[0],
                        expires_at=self._utc(row[1]),
                    )
                    if row is not None
                    else None
                )
            finally:
                cursor.close()

        return result

    def revoke_session(self, token_hash: str) -> bool:
        """Confirm logout only if SQL updates an existing session."""
        with connection_scope(
            write=True,
            connection_factory=self._connection_factory,
        ) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "EXEC dbo.usp_RevokeUserSession @TokenHash=?",
                    token_hash,
                )
                row = cursor.fetchone()

                affected = int(row[0]) if row is not None else 0

                if affected not in (0, 1):
                    raise RuntimeError(
                        "Unexpected session revocation result."
                    )

                result = affected == 1
            finally:
                cursor.close()

        return result

    def update_password_if_current(
        self,
        *,
        user_id: str,
        old_hash: str,
        new_hash: str,
    ) -> bool:
        """Update a password only when the verified hash is still current.

        The Service must verify the current password, enforce the
        password policy, and generate the replacement hash.

        False means the account no longer meets the update conditions.
        """

        if (
            not isinstance(user_id, str)
            or not 1 <= len(user_id) <= 12
        ):
            raise ValueError("Invalid user ID.")

        if (
            not isinstance(old_hash, str)
            or not 1 <= len(old_hash) <= 255
        ):
            raise ValueError("Invalid expected password hash.")

        if (
            not isinstance(new_hash, str)
            or not 1 <= len(new_hash) <= 255
        ):
            raise ValueError("Invalid replacement password hash.")

        with connection_scope(
            write=True,
            connection_factory=self._connection_factory,
        ) as conn:
            cursor = conn.cursor()

            try:
                cursor.execute(
                    """
                    UPDATE dbo.Users
                    SET passwordHash = ?
                    WHERE userId = ?
                      AND passwordHash
                          COLLATE Latin1_General_100_BIN2 = ?
                      AND isLocked = 0
                      AND (
                          EXISTS (
                              SELECT 1
                              FROM dbo.Students
                              WHERE userId = ?
                          )
                          OR EXISTS (
                              SELECT 1
                              FROM dbo.Lecturers
                              WHERE userId = ?
                          )
                      )
                      AND NOT EXISTS (
                          SELECT 1
                          FROM dbo.Administrators
                          WHERE userId = ?
                      )
                    """,
                    new_hash,
                    user_id,
                    old_hash,
                    user_id,
                    user_id,
                    user_id,
                )

                affected = cursor.rowcount

                if affected not in (0, 1):
                    raise RuntimeError(
                        "Unexpected password update result."
                    )

                updated = affected == 1

            finally:
                cursor.close()

        return updated
