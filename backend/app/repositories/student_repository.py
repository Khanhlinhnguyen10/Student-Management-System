
"""Student records repository for Administrator management."""

from dataclasses import dataclass
from datetime import date
from typing import Any, Callable

from app.repositories.transaction import connection_scope


class StudentDuplicateCitizenIdError(ValueError):
    """Citizen ID already belongs to another user."""


class StudentDataIntegrityError(RuntimeError):
    """Student record cannot be changed due to data constraints."""


@dataclass(frozen=True, slots=True)
class StudentRecord:
    """Read-only DTO; not an additional SQL table."""

    studentId: str
    citizenId: str
    fullName: str
    dateOfBirth: date | None
    email: str | None
    gender: str | None
    phoneNumber: str | None
    facultyName: str
    majorName: str
    academicStatus: str
    majorId: str | None = None


_STUDENT_COLUMNS = """
    s.studentId,
    u.citizenId,
    u.fullName,
    u.dateOfBirth,
    u.email,
    u.gender,
    u.phoneNumber,
    f.facultyName,
    m.majorName,
    s.academicStatus,
    s.majorId
"""

_STUDENT_FROM = """
    FROM dbo.Students AS s
    INNER JOIN dbo.Users AS u
        ON u.userId = s.userId
    INNER JOIN dbo.Majors AS m
        ON m.majorId = s.majorId
    INNER JOIN dbo.Faculties AS f
        ON f.facultyId = m.facultyId
"""

_SEARCH_WHERE = """
    WHERE CHARINDEX(?, s.studentId) > 0
       OR CHARINDEX(?, u.fullName) > 0
"""

# Keep pagination in one line for existing unit tests.
_LIST_SQL = (
    "SELECT " + _STUDENT_COLUMNS + _STUDENT_FROM
    + " ORDER BY s.studentId OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
)

_BY_ID_SQL = (
    "SELECT " + _STUDENT_COLUMNS + _STUDENT_FROM
    + " WHERE s.studentId = ?"
)


class StudentRepository:

    def __init__(
        self,
        connection_factory: Callable[[], Any] | None = None,
    ):
        self._connection_factory = connection_factory

    @staticmethod
    def _to_record(row: Any) -> StudentRecord:
        return StudentRecord(*tuple(row))

    @staticmethod
    def _validate_student_id(student_id: str) -> str:

        if (
            not isinstance(student_id, str)
            or not student_id.strip()
            or len(student_id.strip()) > 10
        ):
            raise ValueError(
                "student_id must be a nonempty string up to 10 chars."
            )

        return student_id.strip()

    @staticmethod
    def _validate_search(search: str) -> str:

        if (
            not isinstance(search, str)
            or len(search.strip()) > 100
        ):
            raise ValueError(
                "search must be a string up to 100 characters."
            )

        return search.strip()

    @staticmethod
    def _is_unique_violation(exc: Exception) -> bool:

        message = str(exc)

        return (
            "2601" in message
            or "2627" in message
        )

    @staticmethod
    def _is_foreign_key_violation(exc: Exception) -> bool:

        return "547" in str(exc)

    # =========================================
    # VIEW STUDENT LIST
    # =========================================

    def list_students(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
        search: str = "",
    ) -> list[StudentRecord]:

        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError(
                "limit must be an integer between 1 and 100."
            )

        if type(offset) is not int or offset < 0:
            raise ValueError(
                "offset must be a non-negative integer."
            )

        keyword = self._validate_search(search)

        if keyword:
            sql = (
                "SELECT " + _STUDENT_COLUMNS + _STUDENT_FROM
                + _SEARCH_WHERE
                + " ORDER BY s.studentId OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
            )

            params = (
                keyword,
                keyword,
                offset,
                limit,
            )

        else:
            sql = _LIST_SQL
            params = (offset, limit)

        with connection_scope(
            connection_factory=self._connection_factory
        ) as conn:

            cursor = conn.cursor()

            try:
                cursor.execute(sql, *params)

                rows = cursor.fetchall()

                return [
                    self._to_record(row)
                    for row in rows
                ]

            finally:
                cursor.close()

    # =========================================
    # COUNT STUDENTS
    # =========================================

    def count_students(self, *, search: str = "") -> int:

        keyword = self._validate_search(search)

        sql = "SELECT COUNT_BIG(*) " + _STUDENT_FROM
        params = ()

        if keyword:
            sql += _SEARCH_WHERE
            params = (keyword, keyword)

        with connection_scope(
            connection_factory=self._connection_factory
        ) as conn:

            cursor = conn.cursor()

            try:
                cursor.execute(sql, *params)

                return int(cursor.fetchone()[0])

            finally:
                cursor.close()

    # =========================================
    # VIEW STUDENT DETAILS
    # =========================================

    def get_student_by_id(
        self,
        student_id: str,
    ) -> StudentRecord | None:

        student_id = self._validate_student_id(student_id)

        with connection_scope(
            connection_factory=self._connection_factory
        ) as conn:

            cursor = conn.cursor()

            try:
                cursor.execute(
                    _BY_ID_SQL,
                    student_id,
                )

                row = cursor.fetchone()

                return (
                    self._to_record(row)
                    if row is not None
                    else None
                )

            finally:
                cursor.close()

    # =========================================
    # UPDATE STUDENT RECORD
    # =========================================

    def update_student(
        self,
        *,
        student_id: str,
        citizen_id: str,
        full_name: str,
        date_of_birth: date | None,
        email: str | None,
        gender: str | None,
        phone_number: str | None,
        major_id: str,
        academic_status: str,
    ) -> StudentRecord | None:

        student_id = self._validate_student_id(student_id)

        try:

            with connection_scope(
                write=True,
                connection_factory=self._connection_factory,
            ) as conn:

                cursor = conn.cursor()

                try:

                    # Lock the target student during the update.
                    cursor.execute(
                        """
                        SELECT s.userId
                        FROM dbo.Students AS s
                            WITH (UPDLOCK, HOLDLOCK)
                        WHERE s.studentId = ?
                        """,
                        student_id,
                    )

                    identity = cursor.fetchone()

                    if identity is None:
                        return None

                    user_id = identity[0]

                    # Validate the selected major.
                    cursor.execute(
                        """
                        SELECT TOP (1) 1
                        FROM dbo.Majors
                        WHERE majorId = ?
                        """,
                        major_id,
                    )

                    if cursor.fetchone() is None:
                        raise ValueError(
                            "The selected major does not exist."
                        )

                    # Check Citizen ID uniqueness.
                    cursor.execute(
                        """
                        SELECT TOP (1) 1
                        FROM dbo.Users WITH (UPDLOCK, HOLDLOCK)
                        WHERE citizenId = ?
                          AND userId <> ?
                        """,
                        citizen_id,
                        user_id,
                    )

                    if cursor.fetchone() is not None:
                        raise StudentDuplicateCitizenIdError(
                            "Citizen ID Number already exists."
                        )

                    # Update personal information.
                    cursor.execute(
                        """
                        UPDATE dbo.Users
                        SET
                            citizenId = ?,
                            fullName = ?,
                            dateOfBirth = ?,
                            email = ?,
                            gender = ?,
                            phoneNumber = ?
                        WHERE userId = ?
                        """,
                        citizen_id,
                        full_name,
                        date_of_birth,
                        email,
                        gender,
                        phone_number,
                        user_id,
                    )

                    if cursor.rowcount == 0:
                        raise RuntimeError(
                            "User information update was not confirmed."
                        )

                    # Update student academic information.
                    cursor.execute(
                        """
                        UPDATE dbo.Students
                        SET
                            majorId = ?,
                            academicStatus = ?
                        WHERE studentId = ?
                        """,
                        major_id,
                        academic_status,
                        student_id,
                    )

                    if cursor.rowcount == 0:
                        raise RuntimeError(
                            "Student information update was not confirmed."
                        )

                    # Retrieve the updated record in the same transaction.
                    cursor.execute(
                        _BY_ID_SQL,
                        student_id,
                    )

                    updated_row = cursor.fetchone()

                    if updated_row is None:
                        raise RuntimeError(
                            "Updated student record could not be retrieved."
                        )

                    updated_record = self._to_record(updated_row)

                finally:
                    cursor.close()

            # connection_scope commits before returning.
            return updated_record

        except StudentDuplicateCitizenIdError:
            raise

        except Exception as exc:

            if self._is_unique_violation(exc):
                raise StudentDuplicateCitizenIdError(
                    "Citizen ID Number already exists."
                ) from exc

            if self._is_foreign_key_violation(exc):
                raise StudentDataIntegrityError(
                    "The selected major is invalid or unavailable."
                ) from exc

            raise

    # =========================================
    # DELETE STUDENT RECORD
    # =========================================

    def delete_student(
        self,
        student_id: str,
    ) -> bool:

        student_id = self._validate_student_id(student_id)

        try:

            with connection_scope(
                write=True,
                connection_factory=self._connection_factory,
            ) as conn:

                cursor = conn.cursor()

                try:

                    # Lock the target student.
                    cursor.execute(
                        """
                        SELECT s.userId
                        FROM dbo.Students AS s
                            WITH (UPDLOCK, HOLDLOCK)
                        WHERE s.studentId = ?
                        """,
                        student_id,
                    )

                    identity = cursor.fetchone()

                    if identity is None:
                        return False

                    user_id = identity[0]

                    # Check enrollment dependencies.
                    cursor.execute(
                        """
                        SELECT TOP (1) 1
                        FROM dbo.Enrollments
                        WHERE studentId = ?
                        """,
                        student_id,
                    )

                    if cursor.fetchone() is not None:
                        raise StudentDataIntegrityError(
                            "Cannot delete this student because "
                            "enrollment records are associated with the student."
                        )

                    # Check semester result dependencies.
                    cursor.execute(
                        """
                        SELECT TOP (1) 1
                        FROM dbo.SemesterResults
                        WHERE studentId = ?
                        """,
                        student_id,
                    )

                    if cursor.fetchone() is not None:
                        raise StudentDataIntegrityError(
                            "Cannot delete this student because "
                            "semester result records are associated with the student."
                        )

                    # Delete the student profile first.
                    cursor.execute(
                        """
                        DELETE FROM dbo.Students
                        WHERE studentId = ?
                        """,
                        student_id,
                    )

                    if cursor.rowcount == 0:
                        raise RuntimeError(
                            "Student deletion was not confirmed."
                        )

                    # Delete the associated account.
                    # UserSessions are handled by the existing
                    # ON DELETE CASCADE foreign key.
                    cursor.execute(
                        """
                        DELETE FROM dbo.Users
                        WHERE userId = ?
                        """,
                        user_id,
                    )

                    if cursor.rowcount == 0:
                        raise RuntimeError(
                            "User account deletion was not confirmed."
                        )

                finally:
                    cursor.close()

            # connection_scope commits both deletions together.
            return True

        except StudentDataIntegrityError:
            raise

        except Exception as exc:

            if self._is_foreign_key_violation(exc):
                raise StudentDataIntegrityError(
                    "The student cannot be deleted because "
                    "related records violate database integrity constraints."
                ) from exc

            raise
