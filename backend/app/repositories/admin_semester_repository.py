
"""SQL Server access for Administrator Semester Management (UC20-UC24)."""

from app.repositories.transaction import connection_scope


class SemesterNotFoundError(Exception):
    """Requested semester does not exist."""


class SemesterConflictError(Exception):
    """Semester is duplicated or referenced by academic data."""


LIST_SQL = """
SELECT s.semesterId, s.semesterName, s.academicYear,
       s.startDate, s.endDate,
       (SELECT COUNT(*) FROM dbo.ClassSections AS cs
        WHERE cs.semesterId = s.semesterId) AS classSectionCount,
       (SELECT COUNT(*) FROM dbo.SemesterResults AS sr
        WHERE sr.semesterId = s.semesterId) AS semesterResultCount
FROM dbo.Semesters AS s
ORDER BY s.startDate DESC, s.semesterId DESC;
"""

GET_SQL = """
SELECT s.semesterId, s.semesterName, s.academicYear,
       s.startDate, s.endDate,
       (SELECT COUNT(*) FROM dbo.ClassSections AS cs
        WHERE cs.semesterId = s.semesterId),
       (SELECT COUNT(*) FROM dbo.SemesterResults AS sr
        WHERE sr.semesterId = s.semesterId)
FROM dbo.Semesters AS s
WHERE s.semesterId = ?;
"""

LOCK_SQL = """
SELECT semesterId
FROM dbo.Semesters WITH (UPDLOCK, HOLDLOCK)
WHERE semesterId = ?;
"""

DUPLICATE_SQL = """
SELECT semesterId
FROM dbo.Semesters WITH (UPDLOCK, HOLDLOCK)
WHERE semesterName = ?
  AND (? IS NULL OR semesterId <> ?);
"""

NEXT_ID_SQL = """
SELECT COALESCE(
    MAX(TRY_CONVERT(INT, SUBSTRING(semesterId, 4, 7))), 0
)
FROM dbo.Semesters WITH (TABLOCKX, HOLDLOCK)
WHERE semesterId LIKE
    'SEM[0-9][0-9][0-9][0-9][0-9][0-9][0-9]';
"""

DEPENDENCIES_SQL = """
SELECT CASE WHEN EXISTS (
    SELECT 1
    FROM dbo.ClassSections WITH (HOLDLOCK)
    WHERE semesterId = ?
) OR EXISTS (
    SELECT 1
    FROM dbo.SemesterResults WITH (HOLDLOCK)
    WHERE semesterId = ?
) THEN 1 ELSE 0 END;
"""


def _as_dict(row):
    """Convert a SQL row into a JSON-ready dictionary."""

    return {
        "semesterId": row[0],
        "semesterName": row[1],
        "academicYear": row[2],
        "startDate": row[3].isoformat(),
        "endDate": row[4].isoformat(),
        "classSectionCount": int(row[5]),
        "semesterResultCount": int(row[6]),
    }


def _unique_violation(error):
    """Recognize SQL Server duplicate key errors."""

    return (
        "2627" in str(error)
        or "2601" in str(error)
    )


class AdminSemesterRepository:
    def __init__(self, connection_factory=None):
        self._connection_factory = connection_factory

    # =========================================
    # LIST SEMESTERS
    # =========================================

    def list_semesters(self):
        with connection_scope(
            connection_factory=self._connection_factory
        ) as conn:
            cursor = conn.cursor()

            try:
                cursor.execute(LIST_SQL)

                return [
                    _as_dict(row)
                    for row in cursor.fetchall()
                ]

            finally:
                cursor.close()

    # =========================================
    # GET SEMESTER DETAILS
    # =========================================

    def get_semester(self, semester_id):
        with connection_scope(
            connection_factory=self._connection_factory
        ) as conn:
            cursor = conn.cursor()

            try:
                cursor.execute(
                    GET_SQL,
                    semester_id,
                )

                row = cursor.fetchone()

                return (
                    _as_dict(row)
                    if row is not None
                    else None
                )

            finally:
                cursor.close()

    # =========================================
    # CHECK DUPLICATE SEMESTER NAME
    # =========================================

    @staticmethod
    def _ensure_unique(
        cursor,
        name,
        semester_id=None,
    ):
        cursor.execute(
            DUPLICATE_SQL,
            name,
            semester_id,
            semester_id,
        )

        if cursor.fetchone() is not None:
            raise SemesterConflictError(
                "Semester Name already exists."
            )

    # =========================================
    # LOCK AND VERIFY EXISTING SEMESTER
    # =========================================

    @staticmethod
    def _ensure_exists_locked(
        cursor,
        semester_id,
    ):
        cursor.execute(
            LOCK_SQL,
            semester_id,
        )

        if cursor.fetchone() is None:
            raise SemesterNotFoundError(
                "Semester not found."
            )

    # =========================================
    # CREATE SEMESTER
    # =========================================

    def create_semester(self, fields):
        with connection_scope(
            write=True,
            connection_factory=self._connection_factory,
        ) as conn:
            cursor = conn.cursor()

            try:
                # Protect ID generation with a SQL lock.
                cursor.execute(NEXT_ID_SQL)

                next_number = (
                    int(cursor.fetchone()[0]) + 1
                )

                if next_number > 9999999:
                    raise RuntimeError(
                        "Semester ID range exhausted."
                    )

                semester_id = (
                    f"SEM{next_number:07d}"
                )

                self._ensure_unique(
                    cursor,
                    fields["semesterName"],
                )

                try:
                    cursor.execute(
                        """
                        INSERT INTO dbo.Semesters (
                            semesterId,
                            semesterName,
                            academicYear,
                            startDate,
                            endDate
                        )
                        OUTPUT INSERTED.semesterId
                        VALUES (?, ?, ?, ?, ?);
                        """,
                        semester_id,
                        fields["semesterName"],
                        fields["academicYear"],
                        fields["startDate"],
                        fields["endDate"],
                    )

                    saved = cursor.fetchone()

                except Exception as exc:
                    if _unique_violation(exc):
                        raise SemesterConflictError(
                            "Semester Name already exists."
                        ) from exc

                    raise

                if (
                    saved is None
                    or saved[0] != semester_id
                ):
                    raise RuntimeError(
                        "Semester creation not confirmed."
                    )

                return semester_id

            finally:
                cursor.close()

    # =========================================
    # UPDATE SEMESTER
    # =========================================

    def update_semester(
        self,
        semester_id,
        fields,
    ):
        with connection_scope(
            write=True,
            connection_factory=self._connection_factory,
        ) as conn:
            cursor = conn.cursor()

            try:
                self._ensure_exists_locked(
                    cursor,
                    semester_id,
                )

                self._ensure_unique(
                    cursor,
                    fields["semesterName"],
                    semester_id,
                )

                try:
                    cursor.execute(
                        """
                        UPDATE dbo.Semesters
                        SET
                            semesterName = ?,
                            academicYear = ?,
                            startDate = ?,
                            endDate = ?
                        OUTPUT INSERTED.semesterId
                        WHERE semesterId = ?;
                        """,
                        fields["semesterName"],
                        fields["academicYear"],
                        fields["startDate"],
                        fields["endDate"],
                        semester_id,
                    )

                    saved = cursor.fetchone()

                except Exception as exc:
                    if _unique_violation(exc):
                        raise SemesterConflictError(
                            "Semester Name already exists."
                        ) from exc

                    raise

                if (
                    saved is None
                    or saved[0] != semester_id
                ):
                    raise RuntimeError(
                        "Semester update not confirmed."
                    )

                return semester_id

            finally:
                cursor.close()

    # =========================================
    # DELETE SEMESTER
    # =========================================

    def delete_semester(self, semester_id):
        with connection_scope(
            write=True,
            connection_factory=self._connection_factory,
        ) as conn:
            cursor = conn.cursor()

            try:
                self._ensure_exists_locked(
                    cursor,
                    semester_id,
                )

                # Check linked academic records.
                cursor.execute(
                    DEPENDENCIES_SQL,
                    semester_id,
                    semester_id,
                )

                if bool(cursor.fetchone()[0]):
                    raise SemesterConflictError(
                        "Cannot delete a semester linked "
                        "to class sections or historical "
                        "academic results."
                    )

                # SQL Server foreign keys remain
                # the final protection.
                try:
                    cursor.execute(
                        """
                        DELETE FROM dbo.Semesters
                        OUTPUT DELETED.semesterId
                        WHERE semesterId = ?;
                        """,
                        semester_id,
                    )

                    removed = cursor.fetchone()

                except Exception as exc:
                    if "547" in str(exc):
                        raise SemesterConflictError(
                            "Cannot delete a semester "
                            "linked to academic data."
                        ) from exc

                    raise

                if (
                    removed is None
                    or removed[0] != semester_id
                ):
                    raise RuntimeError(
                        "Semester deletion not confirmed."
                    )

                return True

            finally:
                cursor.close()
