
from app.repositories.transaction import connection_scope


PROFILE_SQL = """
SELECT
    l.lecturerId,
    u.userId,
    u.username,
    u.fullName,
    u.citizenId,
    u.dateOfBirth,
    u.gender,
    u.email,
    u.phoneNumber,
    f.facultyId,
    f.facultyName
FROM dbo.Lecturers AS l
JOIN dbo.Users AS u ON u.userId = l.userId
JOIN dbo.Faculties AS f ON f.facultyId = l.facultyId
WHERE l.userId = ?
  AND u.isLocked = 0
"""


UPDATE_CONTACT_SQL = """
UPDATE u
SET
    email = ?,
    phoneNumber = ?
FROM dbo.Users AS u
JOIN dbo.Lecturers AS l ON l.userId = u.userId
WHERE u.userId = ?
  AND u.isLocked = 0
"""


def profile_dict(row):
    if row is None:
        return None

    return {
        "lecturerId": row[0],
        "userId": row[1],
        "username": row[2],
        "fullName": row[3],
        "citizenId": row[4],
        "dateOfBirth": (
            row[5].isoformat() if row[5] else None
        ),
        "gender": row[6],
        "email": row[7],
        "phoneNumber": row[8],
        "facultyId": row[9],
        "facultyName": row[10],
    }


class LecturerProfileRepository:
    def __init__(self, connection_factory=None):
        self._connection_factory = connection_factory

    def get_profile(self, user_id):
        with connection_scope(
            connection_factory=self._connection_factory
        ) as conn:
            cursor = conn.cursor()

            try:
                cursor.execute(PROFILE_SQL, user_id)
                return profile_dict(cursor.fetchone())
            finally:
                cursor.close()

    def update_contact(self, user_id, email, phone_number):
        with connection_scope(
            write=True,
            connection_factory=self._connection_factory
        ) as conn:
            cursor = conn.cursor()

            try:
                cursor.execute(
                    UPDATE_CONTACT_SQL,
                    email,
                    phone_number,
                    user_id,
                )

                if cursor.rowcount != 1:
                    raise LookupError(
                        "Lecturer profile not found."
                    )

                cursor.execute(PROFILE_SQL, user_id)
                profile = profile_dict(cursor.fetchone())

                if profile is None:
                    raise RuntimeError(
                        "Unable to verify profile update."
                    )

            finally:
                cursor.close()

        return profile
