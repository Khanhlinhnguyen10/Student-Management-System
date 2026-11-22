
"""Student self-service profile data access.

Uses existing Users, Students, Majors and Faculties tables.
No new database tables are introduced.
"""

from typing import Any, Callable

from app.repositories.transaction import connection_scope


_PROFILE_SQL = """
SELECT
    u.username,
    s.studentId,
    u.citizenId,
    u.fullName,
    u.dateOfBirth,
    u.email,
    u.phoneNumber,
    u.gender,
    f.facultyName,
    m.majorName,
    s.academicStatus,
    s.majorId
FROM dbo.Users AS u
INNER JOIN dbo.Students AS s
    ON s.userId = u.userId
INNER JOIN dbo.Majors AS m
    ON m.majorId = s.majorId
INNER JOIN dbo.Faculties AS f
    ON f.facultyId = m.facultyId
WHERE u.userId = ?
"""

_PROFILE_KEYS = (
    "username",
    "studentId",
    "citizenId",
    "fullName",
    "dateOfBirth",
    "email",
    "phoneNumber",
    "gender",
    "facultyName",
    "majorName",
    "academicStatus",
    "majorId",
)

_UPDATE_CONTACT_SQL = """
UPDATE dbo.Users
SET
    email = ?,
    phoneNumber = ?
WHERE userId = ?
  AND EXISTS (
      SELECT 1
      FROM dbo.Students
      WHERE userId = ?
  )
"""


class StudentProfileRepository:
    def __init__(
        self,
        connection_factory: Callable[[], Any] | None = None,
    ):
        self._connection_factory = connection_factory

    @staticmethod
    def _get_profile(cursor, user_id: str) -> dict | None:
        cursor.execute(_PROFILE_SQL, user_id)
        row = cursor.fetchone()

        if row is None:
            return None

        profile = dict(zip(_PROFILE_KEYS, tuple(row)))

        birth_date = profile["dateOfBirth"]
        profile["dateOfBirth"] = (
            birth_date.isoformat()
            if birth_date is not None
            else None
        )

        return profile

    def get_profile(self, user_id: str) -> dict | None:
        with connection_scope(
            connection_factory=self._connection_factory
        ) as conn:
            cursor = conn.cursor()

            try:
                return self._get_profile(cursor, user_id)
            finally:
                cursor.close()

    def update_contact(
        self,
        user_id: str,
        *,
        email: str | None,
        phone_number: str | None,
    ) -> dict | None:
        with connection_scope(
            write=True,
            connection_factory=self._connection_factory,
        ) as conn:
            cursor = conn.cursor()

            try:
                cursor.execute(
                    _UPDATE_CONTACT_SQL,
                    email,
                    phone_number,
                    user_id,
                    user_id,
                )

                if cursor.rowcount == 0:
                    return None

                updated = self._get_profile(cursor, user_id)

                if updated is None:
                    raise RuntimeError(
                        "Updated student profile was not found."
                    )

                return updated
            finally:
                cursor.close()
