
"""Create Account Repository - Student Management System Group 05.

Use Case 11: Create Account.

Uses the existing SQL FINAL schema:
- dbo.Users
- dbo.Students
- dbo.Lecturers
- dbo.Majors
- dbo.Faculties

No new tables or columns.
Account and profile are created within one transaction.
"""

from datetime import date, datetime
from typing import Any, Callable

from app.repositories.transaction import connection_scope


class AccountAlreadyExistsError(ValueError):
    """Username or Citizen ID already exists."""


class AccountReferenceError(ValueError):
    """Selected Major or Faculty does not exist."""


class AccountIdGenerationError(RuntimeError):
    """Unable to generate a unique account identifier."""


# =========================================
# EXISTING ID FORMATS
# =========================================

_ID_CONFIG = {
    "user": (
        "USR",
        9,
        """
        SELECT COALESCE(
            MAX(
                TRY_CONVERT(
                    BIGINT,
                    SUBSTRING(userId, 4, 9)
                )
            ),
            0
        )
        FROM dbo.Users WITH (UPDLOCK, HOLDLOCK)
        WHERE LEFT(userId, 3) = 'USR'
          AND LEN(userId) = 12
          AND SUBSTRING(userId, 4, 9)
              NOT LIKE '%[^0-9]%'
        """,
    ),

    "student": (
        "STU",
        7,
        """
        SELECT COALESCE(
            MAX(
                TRY_CONVERT(
                    BIGINT,
                    SUBSTRING(studentId, 4, 7)
                )
            ),
            0
        )
        FROM dbo.Students WITH (UPDLOCK, HOLDLOCK)
        WHERE LEFT(studentId, 3) = 'STU'
          AND LEN(studentId) = 10
          AND SUBSTRING(studentId, 4, 7)
              NOT LIKE '%[^0-9]%'
        """,
    ),

    "lecturer": (
        "LEC",
        7,
        """
        SELECT COALESCE(
            MAX(
                TRY_CONVERT(
                    BIGINT,
                    SUBSTRING(lecturerId, 4, 7)
                )
            ),
            0
        )
        FROM dbo.Lecturers WITH (UPDLOCK, HOLDLOCK)
        WHERE LEFT(lecturerId, 3) = 'LEC'
          AND LEN(lecturerId) = 10
          AND SUBSTRING(lecturerId, 4, 7)
              NOT LIKE '%[^0-9]%'
        """,
    ),
}


class CreateAccountRepository:
    """Repository for Student and Lecturer account creation."""

    def __init__(
        self,
        connection_factory: Callable[[], Any] | None = None,
    ):
        self._connection_factory = connection_factory

    # =========================================
    # HELPERS
    # =========================================

    @staticmethod
    def _required(value, field_name: str) -> str:
        if not isinstance(value, str):
            raise ValueError(
                f"{field_name} is required."
            )

        value = value.strip()

        if not value:
            raise ValueError(
                f"{field_name} is required."
            )

        return value

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
    # LIST FACULTIES
    # =========================================

    def list_faculties(self) -> list[dict]:
        sql = """
            SELECT
                facultyId,
                facultyName
            FROM dbo.Faculties
            ORDER BY facultyName, facultyId
        """

        with connection_scope(
            connection_factory=self._connection_factory,
        ) as conn:

            cursor = conn.cursor()

            try:
                cursor.execute(sql)

                return [
                    {
                        "facultyId": row[0],
                        "facultyName": row[1],
                    }
                    for row in cursor.fetchall()
                ]

            finally:
                cursor.close()

    # =========================================
    # LIST MAJORS
    # =========================================

    def list_majors(self) -> list[dict]:
        sql = """
            SELECT
                m.majorId,
                m.majorName,
                m.facultyId,
                f.facultyName
            FROM dbo.Majors AS m
            INNER JOIN dbo.Faculties AS f
                ON f.facultyId = m.facultyId
            ORDER BY
                f.facultyName,
                m.majorName,
                m.majorId
        """

        with connection_scope(
            connection_factory=self._connection_factory,
        ) as conn:

            cursor = conn.cursor()

            try:
                cursor.execute(sql)

                return [
                    {
                        "majorId": row[0],
                        "majorName": row[1],
                        "facultyId": row[2],
                        "facultyName": row[3],
                    }
                    for row in cursor.fetchall()
                ]

            finally:
                cursor.close()

    # =========================================
    # TRANSACTION-LEVEL APPLICATION LOCK
    # =========================================

    @staticmethod
    def _acquire_creation_lock(cursor) -> None:
        """Prevent concurrent requests from generating duplicate IDs."""

        cursor.execute(
            """
            SET NOCOUNT ON;

            DECLARE @lock_result INT;

            EXEC @lock_result = sys.sp_getapplock
                @Resource = ?,
                @LockMode = 'Exclusive',
                @LockOwner = 'Transaction',
                @LockTimeout = 8000;

            SELECT @lock_result AS LockResult;
            """,
            "SMS_Group05_CreateAccount_IDs",
        )

        while cursor.description is None:
            if not cursor.nextset():
                raise AccountIdGenerationError(
                    "Unable to obtain account creation lock."
                )

        row = cursor.fetchone()

        if row is None or int(row[0]) < 0:
            raise AccountIdGenerationError(
                "Account creation is busy. Please retry."
            )

    # =========================================
    # GENERATE IDENTIFIERS
    # =========================================

    @staticmethod
    def _next_id(cursor, id_type: str) -> str:
        prefix, digits, sql = _ID_CONFIG[id_type]

        cursor.execute(sql)

        row = cursor.fetchone()

        if row is None:
            raise AccountIdGenerationError(
                "Unable to read the current identifier."
            )

        next_number = int(row[0]) + 1

        if next_number > 10 ** digits - 1:
            raise AccountIdGenerationError(
                "Identifier capacity exceeded."
            )

        return f"{prefix}{next_number:0{digits}d}"

    # =========================================
    # CHECK UNIQUE FIELDS
    # =========================================

    @staticmethod
    def _check_unique_identity(
        cursor,
        *,
        username: str,
        citizen_id: str,
    ) -> None:

        cursor.execute(
            """
            SELECT TOP (1) 1
            FROM dbo.Users WITH (UPDLOCK, HOLDLOCK)
            WHERE username = ?
            """,
            username,
        )

        if cursor.fetchone() is not None:
            raise AccountAlreadyExistsError(
                "Username already exists."
            )

        cursor.execute(
            """
            SELECT TOP (1) 1
            FROM dbo.Users WITH (UPDLOCK, HOLDLOCK)
            WHERE citizenId = ?
            """,
            citizen_id,
        )

        if cursor.fetchone() is not None:
            raise AccountAlreadyExistsError(
                "Citizen ID Number already exists."
            )

    # =========================================
    # CHECK ACADEMIC REFERENCES
    # =========================================

    @staticmethod
    def _check_academic_reference(
        cursor,
        *,
        account_type: str,
        major_id: str | None,
        faculty_id: str | None,
    ) -> None:

        if account_type == "Student":
            cursor.execute(
                """
                SELECT TOP (1) 1
                FROM dbo.Majors WITH (HOLDLOCK)
                WHERE majorId = ?
                """,
                major_id,
            )

            if cursor.fetchone() is None:
                raise AccountReferenceError(
                    "Selected major does not exist."
                )

        else:
            cursor.execute(
                """
                SELECT TOP (1) 1
                FROM dbo.Faculties WITH (HOLDLOCK)
                WHERE facultyId = ?
                """,
                faculty_id,
            )

            if cursor.fetchone() is None:
                raise AccountReferenceError(
                    "Selected faculty does not exist."
                )

    # =========================================
    # CREATE ACCOUNT
    # =========================================

    def create_account(
        self,
        *,
        account_type: str,
        username: str,
        password_hash: str,
        citizen_id: str,
        full_name: str,
        date_of_birth: date | None = None,
        email: str | None = None,
        phone_number: str | None = None,
        gender: str | None = None,
        major_id: str | None = None,
        faculty_id: str | None = None,
        academic_status: str | None = None,
    ) -> dict:

        # -------------------------------------
        # 1. Validate database input
        # -------------------------------------

        if account_type not in ("Student", "Lecturer"):
            raise ValueError(
                "Account type must be Student or Lecturer."
            )

        username = self._required(
            username, "Username"
        )

        password_hash = self._required(
            password_hash, "Password hash"
        )

        citizen_id = self._required(
            citizen_id, "Citizen ID"
        )

        full_name = self._required(
            full_name, "Full name"
        )

        for field_name, value, max_length in (
            ("Username", username, 50),
            ("Password hash", password_hash, 255),
            ("Citizen ID", citizen_id, 12),
            ("Full name", full_name, 200),
        ):
            if len(value) > max_length:
                raise ValueError(
                    f"{field_name} exceeds {max_length} characters."
                )

        if date_of_birth is not None and (
            not isinstance(date_of_birth, date)
            or isinstance(date_of_birth, datetime)
        ):
            raise ValueError(
                "Date of birth must be a date."
            )

        for field_name, value, max_length in (
            ("Email", email, 100),
            ("Phone number", phone_number, 15),
            ("Gender", gender, 20),
        ):
            if value is not None and (
                not isinstance(value, str)
                or len(value) > max_length
            ):
                raise ValueError(
                    f"{field_name} is invalid."
                )

        if account_type == "Student":
            major_id = self._required(
                major_id, "Major ID"
            )

            academic_status = self._required(
                academic_status, "Academic status"
            )

            if len(major_id) > 10:
                raise ValueError(
                    "Major ID exceeds 10 characters."
                )

            if len(academic_status) > 60:
                raise ValueError(
                    "Academic status exceeds 60 characters."
                )

            if faculty_id is not None:
                raise ValueError(
                    "Faculty ID is not accepted for Student accounts."
                )

        else:
            faculty_id = self._required(
                faculty_id, "Faculty ID"
            )

            if len(faculty_id) > 10:
                raise ValueError(
                    "Faculty ID exceeds 10 characters."
                )

            if major_id is not None:
                raise ValueError(
                    "Major ID is not accepted for Lecturer accounts."
                )

            if academic_status is not None:
                raise ValueError(
                    "Academic status is not accepted for Lecturer accounts."
                )

        # -------------------------------------
        # 2. Atomic SQL transaction
        # -------------------------------------

        try:
            with connection_scope(
                write=True,
                connection_factory=self._connection_factory,
            ) as conn:

                cursor = conn.cursor()

                try:
                    self._acquire_creation_lock(cursor)

                    self._check_unique_identity(
                        cursor,
                        username=username,
                        citizen_id=citizen_id,
                    )

                    self._check_academic_reference(
                        cursor,
                        account_type=account_type,
                        major_id=major_id,
                        faculty_id=faculty_id,
                    )

                    user_id = self._next_id(
                        cursor, "user"
                    )

                    profile_id = self._next_id(
                        cursor,
                        "student"
                        if account_type == "Student"
                        else "lecturer",
                    )

                    # ---------------------------------
                    # 3. Create Users record
                    # ---------------------------------

                    cursor.execute(
                        """
                        INSERT INTO dbo.Users (
                            userId,
                            username,
                            passwordHash,
                            isLocked,
                            citizenId,
                            fullName,
                            dateOfBirth,
                            email,
                            phoneNumber,
                            gender
                        )
                        VALUES (
                            ?, ?, ?, 0, ?, ?, ?, ?, ?, ?
                        )
                        """,
                        user_id,
                        username,
                        password_hash,
                        citizen_id,
                        full_name,
                        date_of_birth,
                        email,
                        phone_number,
                        gender,
                    )

                    # ---------------------------------
                    # 4. Create role-specific profile
                    # ---------------------------------

                    if account_type == "Student":
                        cursor.execute(
                            """
                            INSERT INTO dbo.Students (
                                studentId,
                                userId,
                                majorId,
                                academicStatus
                            )
                            VALUES (?, ?, ?, ?)
                            """,
                            profile_id,
                            user_id,
                            major_id,
                            academic_status,
                        )

                    else:
                        cursor.execute(
                            """
                            INSERT INTO dbo.Lecturers (
                                lecturerId,
                                userId,
                                facultyId
                            )
                            VALUES (?, ?, ?)
                            """,
                            profile_id,
                            user_id,
                            faculty_id,
                        )

                    result = {
                        "accountType": account_type,
                        "userId": user_id,
                        "username": username,
                        "fullName": full_name,
                        "studentId": (
                            profile_id
                            if account_type == "Student"
                            else None
                        ),
                        "lecturerId": (
                            profile_id
                            if account_type == "Lecturer"
                            else None
                        ),
                    }

                finally:
                    cursor.close()

            # Both INSERTs are committed together.
            return result

        # -------------------------------------
        # 5. Database error mapping
        # -------------------------------------

        except (
            AccountAlreadyExistsError,
            AccountReferenceError,
            AccountIdGenerationError,
        ):
            raise

        except Exception as exc:
            if self._is_unique_violation(exc):
                raise AccountAlreadyExistsError(
                    "Username, Citizen ID, or generated ID already exists."
                ) from exc

            if self._is_foreign_key_violation(exc):
                raise AccountReferenceError(
                    "Selected academic record is invalid."
                ) from exc

            raise
