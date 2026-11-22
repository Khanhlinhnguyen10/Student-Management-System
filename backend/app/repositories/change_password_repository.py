
"""Change Password Repository - Group 05.

Accesses dbo.Users in SQL Server.

Responsibilities:
- Read the existing password hash.
- Update the hash using an atomic condition.
- Commit only after a successful update.
- Roll back when a database operation fails.
"""

from typing import Any, Callable

from app.repositories.transaction import connection_scope


class ChangePasswordRepository:
    def __init__(
        self,
        connection_factory: Callable[[], Any] | None = None,
    ):
        self._connection_factory = connection_factory

    # =========================================
    # READ CURRENT PASSWORD HASH
    # =========================================

    def get_password_hash(
        self,
        user_id: str,
    ) -> str | None:
        sql = """
            SELECT passwordHash
            FROM dbo.Users
            WHERE userId = ?
              AND isLocked = 0
        """

        with connection_scope(
            connection_factory=self._connection_factory
        ) as conn:

            cursor = conn.cursor()

            try:
                cursor.execute(
                    sql,
                    user_id,
                )

                row = cursor.fetchone()

                if row is None:
                    return None

                return row[0]

            finally:
                cursor.close()

    # =========================================
    # ATOMIC PASSWORD HASH UPDATE
    # =========================================

    def replace_password_hash_if_unchanged(
        self,
        user_id: str,
        old_hash: str,
        new_hash: str,
    ) -> bool:
        """Prevent Lost Update using the previously verified hash.

        A successful update is committed by connection_scope.
        If the expected hash no longer matches, no row is updated.
        """

        sql = """
            UPDATE dbo.Users
            SET passwordHash = ?
            OUTPUT inserted.userId
            WHERE userId = ?
              AND passwordHash
                  COLLATE Latin1_General_100_BIN2 = ?
              AND isLocked = 0
        """

        with connection_scope(
            write=True,
            connection_factory=self._connection_factory,
        ) as conn:

            cursor = conn.cursor()

            try:
                cursor.execute(
                    sql,
                    new_hash,
                    user_id,
                    old_hash,
                )

                updated_row = cursor.fetchone()

                updated = updated_row is not None

            finally:
                cursor.close()

        # The transaction has completed before returning.
        return updated
