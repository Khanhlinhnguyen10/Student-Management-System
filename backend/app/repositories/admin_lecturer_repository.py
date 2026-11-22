
"""Administrator Lecturer Management Repository.

Student Management System - Group 05.

Handles:
- View lecturer list
- Count lecturers
- View lecturer details
- List faculty options
- Update lecturer profile
- Delete lecturer profile

Uses existing SQL Server tables:
- dbo.Users
- dbo.Lecturers
- dbo.Faculties
- dbo.ClassSections
- dbo.UserSessions

No schema modifications.
"""

from dataclasses import dataclass
from datetime import date
from typing import Any, Callable

from app.repositories.transaction import connection_scope


# =========================================
# REPOSITORY EXCEPTIONS
# =========================================

class LecturerDuplicateIdentityError(ValueError):
    """Citizen ID already belongs to another user."""


class LecturerDataIntegrityError(RuntimeError):
    """Lecturer operation violates data integrity."""


# =========================================
# DATA TRANSFER OBJECT
# =========================================

@dataclass(frozen=True, slots=True)
class LecturerRecord:
    """Read-only lecturer record, not a SQL table."""

    lecturerId: str
    citizenId: str
    fullName: str
    dateOfBirth: date | None
    email: str | None
    gender: str | None
    phoneNumber: str | None
    facultyId: str
    facultyName: str


# =========================================
# REUSABLE SQL FRAGMENTS
# =========================================

_LECTURER_COLUMNS = """
    l.lecturerId,
    u.citizenId,
    u.fullName,
    u.dateOfBirth,
    u.email,
    u.gender,
    u.phoneNumber,
    l.facultyId,
    f.facultyName
"""

_LECTURER_FROM = """
    FROM dbo.Lecturers AS l
    INNER JOIN dbo.Users AS u
        ON u.userId = l.userId
    INNER JOIN dbo.Faculties AS f
        ON f.facultyId = l.facultyId
"""

_SEARCH_WHERE = """
    WHERE CHARINDEX(?, l.lecturerId) > 0
       OR CHARINDEX(?, u.fullName) > 0
"""

_LIST_SQL = (
    "SELECT "
    + _LECTURER_COLUMNS
    + _LECTURER_FROM
    + " ORDER BY l.lecturerId OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
)

_BY_ID_SQL = (
    "SELECT "
    + _LECTURER_COLUMNS
    + _LECTURER_FROM
    + " WHERE l.lecturerId = ?"
)


# =========================================
# ADMIN LECTURER REPOSITORY
# =========================================

class AdminLecturerRepository:

    def __init__(
        self,
        connection_factory: Callable[[], Any] | None = None,
    ):
        self._connection_factory = connection_factory

    # =====================================
    # HELPER METHODS
    # =====================================

    @staticmethod
    def _to_record(row: Any) -> LecturerRecord:
        return LecturerRecord(*tuple(row))

    @staticmethod
    def _validate_lecturer_id(lecturer_id: str) -> str:
        if (
            not isinstance(lecturer_id, str)
            or not lecturer_id.strip()
            or len(lecturer_id.strip()) > 10
        ):
            raise ValueError(
                "lecturer_id must be a nonempty "
                "string up to 10 characters."
            )

        return lecturer_id.strip()

    @staticmethod
    def _validate_search(search: str) -> str:
        if (
            not isinstance(search, str)
            or len(search.strip()) > 100
        ):
            raise ValueError(
                "search must be a string "
                "up to 100 characters."
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

    # =====================================
    # VIEW LECTURER LIST
    # =====================================

    def list_lecturers(
        self,
        *,
        limit: int = 10,
        offset: int = 0,
        search: str = "",
    ) -> list[LecturerRecord]:

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
                "SELECT "
                + _LECTURER_COLUMNS
                + _LECTURER_FROM
                + _SEARCH_WHERE
                + " ORDER BY l.lecturerId OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
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

    # =====================================
    # COUNT LECTURERS
    # =====================================

    def count_lecturers(
        self,
        *,
        search: str = "",
    ) -> int:

        keyword = self._validate_search(search)

        sql = (
            "SELECT COUNT_BIG(*) "
            + _LECTURER_FROM
        )

        params = ()

        if keyword:
            sql += _SEARCH_WHERE

            params = (
                keyword,
                keyword,
            )

        with connection_scope(
            connection_factory=self._connection_factory
        ) as conn:

            cursor = conn.cursor()

            try:
                cursor.execute(sql, *params)

                row = cursor.fetchone()

                return int(row[0])

            finally:
                cursor.close()

    # =====================================
    # VIEW LECTURER DETAILS
    # =====================================

    def get_lecturer_by_id(
        self,
        lecturer_id: str,
    ) -> LecturerRecord | None:

        lecturer_id = self._validate_lecturer_id(
            lecturer_id
        )

        with connection_scope(
            connection_factory=self._connection_factory
        ) as conn:

            cursor = conn.cursor()

            try:
                cursor.execute(
                    _BY_ID_SQL,
                    lecturer_id,
                )

                row = cursor.fetchone()

                return (
                    self._to_record(row)
                    if row is not None
                    else None
                )

            finally:
                cursor.close()

    # =====================================
    # LIST FACULTY OPTIONS
    # =====================================

    def list_faculty_options(self) -> list[dict]:

        sql = """
            SELECT
                facultyId,
                facultyName
            FROM dbo.Faculties
            ORDER BY facultyName, facultyId
        """

        with connection_scope(
            connection_factory=self._connection_factory
        ) as conn:

            cursor = conn.cursor()

            try:
                cursor.execute(sql)

                rows = cursor.fetchall()

                return [
                    {
                        "facultyId": row[0],
                        "facultyName": row[1],
                    }
                    for row in rows
                ]

            finally:
                cursor.close()

    # =====================================
    # UPDATE LECTURER PROFILE
    # =====================================

    def update_lecturer(
        self,
        *,
        lecturer_id: str,
        citizen_id: str,
        full_name: str,
        date_of_birth: date | None,
        email: str | None,
        gender: str | None,
        phone_number: str | None,
        faculty_id: str,
    ) -> LecturerRecord | None:

        lecturer_id = self._validate_lecturer_id(
            lecturer_id
        )

        try:

            with connection_scope(
                write=True,
                connection_factory=self._connection_factory,
            ) as conn:

                cursor = conn.cursor()

                try:

                    # 1. Lock lecturer record.
                    cursor.execute(
                        """
                        SELECT userId
                        FROM dbo.Lecturers
                            WITH (UPDLOCK, HOLDLOCK)
                        WHERE lecturerId = ?
                        """,
                        lecturer_id,
                    )

                    identity = cursor.fetchone()

                    if identity is None:
                        return None

                    user_id = identity[0]

                    # 2. Validate selected faculty.
                    cursor.execute(
                        """
                        SELECT TOP (1) 1
                        FROM dbo.Faculties
                        WHERE facultyId = ?
                        """,
                        faculty_id,
                    )

                    if cursor.fetchone() is None:
                        raise ValueError(
                            "The selected faculty does not exist."
                        )

                    # 3. Check Citizen ID uniqueness.
                    cursor.execute(
                        """
                        SELECT TOP (1) 1
                        FROM dbo.Users
                            WITH (UPDLOCK, HOLDLOCK)
                        WHERE citizenId = ?
                          AND userId <> ?
                        """,
                        citizen_id,
                        user_id,
                    )

                    if cursor.fetchone() is not None:
                        raise LecturerDuplicateIdentityError(
                            "Citizen ID Number already exists."
                        )

                    # 4. Update personal information.
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
                            "User information update "
                            "was not confirmed."
                        )

                    # 5. Update lecturer faculty.
                    cursor.execute(
                        """
                        UPDATE dbo.Lecturers
                        SET facultyId = ?
                        WHERE lecturerId = ?
                        """,
                        faculty_id,
                        lecturer_id,
                    )

                    if cursor.rowcount == 0:
                        raise RuntimeError(
                            "Lecturer information update "
                            "was not confirmed."
                        )

                    # 6. Retrieve updated record.
                    cursor.execute(
                        _BY_ID_SQL,
                        lecturer_id,
                    )

                    updated_row = cursor.fetchone()

                    if updated_row is None:
                        raise RuntimeError(
                            "Updated lecturer record "
                            "could not be retrieved."
                        )

                    updated_record = self._to_record(
                        updated_row
                    )

                finally:
                    cursor.close()

            # The transaction has committed.
            return updated_record

        except LecturerDuplicateIdentityError:
            raise

        except LecturerDataIntegrityError:
            raise

        except Exception as exc:

            if self._is_unique_violation(exc):
                raise LecturerDuplicateIdentityError(
                    "Citizen ID Number already exists."
                ) from exc

            if self._is_foreign_key_violation(exc):
                raise LecturerDataIntegrityError(
                    "The selected faculty is invalid "
                    "or unavailable."
                ) from exc

            raise

    # =====================================
    # DELETE LECTURER PROFILE
    # =====================================

    def delete_lecturer(
        self,
        lecturer_id: str,
    ) -> bool:

        lecturer_id = self._validate_lecturer_id(
            lecturer_id
        )

        try:

            with connection_scope(
                write=True,
                connection_factory=self._connection_factory,
            ) as conn:

                cursor = conn.cursor()

                try:

                    # 1. Lock lecturer record.
                    cursor.execute(
                        """
                        SELECT userId
                        FROM dbo.Lecturers
                            WITH (UPDLOCK, HOLDLOCK)
                        WHERE lecturerId = ?
                        """,
                        lecturer_id,
                    )

                    identity = cursor.fetchone()

                    if identity is None:
                        return False

                    user_id = identity[0]

                    # 2. Check class-section dependencies.
                    cursor.execute(
                        """
                        SELECT TOP (1) 1
                        FROM dbo.ClassSections
                        WHERE lecturerId = ?
                        """,
                        lecturer_id,
                    )

                    if cursor.fetchone() is not None:
                        raise LecturerDataIntegrityError(
                            "Cannot delete this lecturer "
                            "because assigned class sections "
                            "are associated with the lecturer."
                        )

                    # 3. Delete lecturer profile.
                    cursor.execute(
                        """
                        DELETE FROM dbo.Lecturers
                        WHERE lecturerId = ?
                        """,
                        lecturer_id,
                    )

                    if cursor.rowcount == 0:
                        raise RuntimeError(
                            "Lecturer deletion "
                            "was not confirmed."
                        )

                    # 4. Remove active sessions for
                    # the associated user account.
                    cursor.execute(
                        """
                        DELETE FROM dbo.UserSessions
                        WHERE userId = ?
                        """,
                        user_id,
                    )

                    # 5. Delete associated user account.
                    cursor.execute(
                        """
                        DELETE FROM dbo.Users
                        WHERE userId = ?
                        """,
                        user_id,
                    )

                    if cursor.rowcount == 0:
                        raise RuntimeError(
                            "User account deletion "
                            "was not confirmed."
                        )

                finally:
                    cursor.close()

            # All related operations have committed.
            return True

        except LecturerDataIntegrityError:
            raise

        except Exception as exc:

            if self._is_foreign_key_violation(exc):
                raise LecturerDataIntegrityError(
                    "Cannot delete lecturer because "
                    "related records exist."
                ) from exc

            raise
