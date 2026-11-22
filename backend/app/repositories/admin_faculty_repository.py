
"""SQL Server repository for Faculty Management - UC25 to UC29."""

from app.repositories.transaction import connection_scope


class FacultyNotFoundError(Exception):
    """Faculty record does not exist."""


class FacultyConflictError(Exception):
    """Faculty has duplicate data or linked academic records."""


FACULTY_COLUMNS = """
    f.facultyId,
    f.facultyCode,
    f.facultyName,
    f.email,
    f.phoneNumber,
    (
        SELECT COUNT(*)
        FROM dbo.Majors AS m
        WHERE m.facultyId = f.facultyId
    ) AS majorCount,
    (
        SELECT COUNT(*)
        FROM dbo.Lecturers AS l
        WHERE l.facultyId = f.facultyId
    ) AS lecturerCount,
    (
        SELECT COUNT(*)
        FROM dbo.Courses AS c
        WHERE c.facultyId = f.facultyId
    ) AS courseCount
"""

LIST_SQL = f"""
SELECT {FACULTY_COLUMNS}
FROM dbo.Faculties AS f
ORDER BY f.facultyName, f.facultyCode;
"""

GET_SQL = f"""
SELECT {FACULTY_COLUMNS}
FROM dbo.Faculties AS f
WHERE f.facultyId = ?;
"""

LOCK_SQL = """
SELECT facultyId
FROM dbo.Faculties WITH (UPDLOCK, HOLDLOCK)
WHERE facultyId = ?;
"""

DUPLICATE_SQL = """
SELECT facultyId
FROM dbo.Faculties WITH (UPDLOCK, HOLDLOCK)
WHERE facultyCode = ?;
"""

NEXT_ID_SQL = """
SELECT COALESCE(
    MAX(TRY_CONVERT(INT, SUBSTRING(facultyId, 4, 7))),
    0
)
FROM dbo.Faculties WITH (TABLOCKX, HOLDLOCK)
WHERE facultyId LIKE
    'FAC[0-9][0-9][0-9][0-9][0-9][0-9][0-9]';
"""

DEPENDENCIES_SQL = """
SELECT
    (
        SELECT COUNT(*)
        FROM dbo.Majors WITH (UPDLOCK, HOLDLOCK)
        WHERE facultyId = ?
    ),
    (
        SELECT COUNT(*)
        FROM dbo.Lecturers WITH (UPDLOCK, HOLDLOCK)
        WHERE facultyId = ?
    ),
    (
        SELECT COUNT(*)
        FROM dbo.Courses WITH (UPDLOCK, HOLDLOCK)
        WHERE facultyId = ?
    );
"""


def _faculty_dict(row):
    """Convert one SQL row to a JSON-compatible dictionary."""

    return {
        "facultyId": row[0],
        "facultyCode": row[1],
        "facultyName": row[2],
        "email": row[3],
        "phoneNumber": row[4],
        "majorCount": int(row[5]),
        "lecturerCount": int(row[6]),
        "courseCount": int(row[7]),
    }


def _is_duplicate_error(exc):
    message = str(exc)
    return "2627" in message or "2601" in message


def _is_foreign_key_error(exc):
    return "547" in str(exc)


class AdminFacultyRepository:
    def __init__(self, connection_factory=None):
        self._connection_factory = connection_factory

    # =========================================
    # LIST FACULTIES
    # =========================================

    def list_faculties(self):
        with connection_scope(
            connection_factory=self._connection_factory
        ) as conn:
            cursor = conn.cursor()

            try:
                cursor.execute(LIST_SQL)

                return [
                    _faculty_dict(row)
                    for row in cursor.fetchall()
                ]

            finally:
                cursor.close()

    # =========================================
    # GET FACULTY DETAILS
    # =========================================

    def get_faculty(self, faculty_id):
        with connection_scope(
            connection_factory=self._connection_factory
        ) as conn:
            cursor = conn.cursor()

            try:
                cursor.execute(
                    GET_SQL,
                    faculty_id,
                )

                row = cursor.fetchone()

                return (
                    _faculty_dict(row)
                    if row is not None
                    else None
                )

            finally:
                cursor.close()

    # =========================================
    # INTERNAL VALIDATION
    # =========================================

    @staticmethod
    def _ensure_exists(cursor, faculty_id):
        cursor.execute(
            LOCK_SQL,
            faculty_id,
        )

        if cursor.fetchone() is None:
            raise FacultyNotFoundError(
                "Faculty not found."
            )

    @staticmethod
    def _ensure_unique(cursor, faculty_code):
        cursor.execute(
            DUPLICATE_SQL,
            faculty_code,
        )

        if cursor.fetchone() is not None:
            raise FacultyConflictError(
                "Faculty Code already exists."
            )

    # =========================================
    # CREATE FACULTY
    # =========================================

    def create_faculty(self, fields):
        with connection_scope(
            write=True,
            connection_factory=self._connection_factory,
        ) as conn:
            cursor = conn.cursor()

            try:
                # Lock the table while generating the next ID.
                cursor.execute(NEXT_ID_SQL)

                row = cursor.fetchone()

                number = int(row[0]) + 1

                if number > 9999999:
                    raise RuntimeError(
                        "Faculty ID range exhausted."
                    )

                faculty_id = f"FAC{number:07d}"

                self._ensure_unique(
                    cursor,
                    fields["facultyCode"],
                )

                try:
                    cursor.execute(
                        """
                        INSERT INTO dbo.Faculties (
                            facultyId,
                            facultyCode,
                            facultyName,
                            email,
                            phoneNumber
                        )
                        OUTPUT INSERTED.facultyId
                        VALUES (?, ?, ?, ?, ?);
                        """,
                        faculty_id,
                        fields["facultyCode"],
                        fields["facultyName"],
                        fields["email"],
                        fields["phoneNumber"],
                    )

                    saved = cursor.fetchone()

                except Exception as exc:
                    if _is_duplicate_error(exc):
                        raise FacultyConflictError(
                            "Faculty Code already exists."
                        ) from exc

                    raise

                if (
                    saved is None
                    or saved[0] != faculty_id
                ):
                    raise RuntimeError(
                        "Faculty creation not confirmed."
                    )

                return faculty_id

            finally:
                cursor.close()

    # =========================================
    # UPDATE FACULTY
    # =========================================

    def update_faculty(self, faculty_id, fields):
        with connection_scope(
            write=True,
            connection_factory=self._connection_factory,
        ) as conn:
            cursor = conn.cursor()

            try:
                self._ensure_exists(
                    cursor,
                    faculty_id,
                )

                # Faculty Code cannot be changed.
                # Update only Name, Email and Phone Number.
                cursor.execute(
                    """
                    UPDATE dbo.Faculties
                    SET facultyName = ?,
                        email = ?,
                        phoneNumber = ?
                    OUTPUT INSERTED.facultyId
                    WHERE facultyId = ?;
                    """,
                    fields["facultyName"],
                    fields["email"],
                    fields["phoneNumber"],
                    faculty_id,
                )

                saved = cursor.fetchone()

                if (
                    saved is None
                    or saved[0] != faculty_id
                ):
                    raise RuntimeError(
                        "Faculty update not confirmed."
                    )

                return faculty_id

            finally:
                cursor.close()

    # =========================================
    # DELETE FACULTY
    # =========================================

    def delete_faculty(self, faculty_id):
        with connection_scope(
            write=True,
            connection_factory=self._connection_factory,
        ) as conn:
            cursor = conn.cursor()

            try:
                self._ensure_exists(
                    cursor,
                    faculty_id,
                )

                # Check all three real foreign-key references.
                cursor.execute(
                    DEPENDENCIES_SQL,
                    faculty_id,
                    faculty_id,
                    faculty_id,
                )

                row = cursor.fetchone()

                if row is None:
                    raise RuntimeError(
                        "Unable to check faculty references."
                    )

                major_count = int(row[0])
                lecturer_count = int(row[1])
                course_count = int(row[2])

                if (
                    major_count > 0
                    or lecturer_count > 0
                    or course_count > 0
                ):
                    raise FacultyConflictError(
                        "Cannot delete a faculty linked "
                        "to majors, lecturers or courses."
                    )

                try:
                    cursor.execute(
                        """
                        DELETE FROM dbo.Faculties
                        OUTPUT DELETED.facultyId
                        WHERE facultyId = ?;
                        """,
                        faculty_id,
                    )

                    deleted = cursor.fetchone()

                except Exception as exc:
                    if _is_foreign_key_error(exc):
                        raise FacultyConflictError(
                            "Cannot delete a faculty "
                            "linked to academic data."
                        ) from exc

                    raise

                if (
                    deleted is None
                    or deleted[0] != faculty_id
                ):
                    raise RuntimeError(
                        "Faculty deletion not confirmed."
                    )

                return True

            finally:
                cursor.close()
