
"""Create Account Service - Student Management System Group 05.

Use Case 11 - Create Account.

Validate required fields, generate initial credentials,
hash passwords, and delegate atomic database creation
to CreateAccountRepository.

No SQL statements or new business tables.
"""

from datetime import date, datetime
import re
import secrets
import string

from werkzeug.security import generate_password_hash

from app.repositories.create_account_repository import (
    CreateAccountRepository,
)


class CreateAccountValidationError(ValueError):
    """Invalid account creation input."""


class CreateAccountService:
    COMMON_FIELDS = {
        "accountType",
        "username",
        "citizenId",
        "fullName",
        "dateOfBirth",
        "email",
        "phoneNumber",
        "gender",
    }

    STUDENT_FIELDS = COMMON_FIELDS | {
        "majorId",
        "academicStatus",
    }

    LECTURER_FIELDS = COMMON_FIELDS | {
        "facultyId",
    }

    def __init__(
        self,
        repository: CreateAccountRepository | None = None,
    ):
        self._repo = (
            repository
            if repository is not None
            else CreateAccountRepository()
        )

    # =========================================
    # REQUIRED TEXT
    # =========================================

    @staticmethod
    def _required_text(
        value,
        field_name: str,
        max_length: int,
    ) -> str:
        if not isinstance(value, str):
            raise CreateAccountValidationError(
                f"{field_name} is required."
            )

        value = value.strip()

        if not value:
            raise CreateAccountValidationError(
                f"{field_name} is required."
            )

        if len(value) > max_length:
            raise CreateAccountValidationError(
                f"{field_name} exceeds {max_length} characters."
            )

        return value

    # =========================================
    # REQUIRED DATE OF BIRTH
    # =========================================

    @staticmethod
    def _parse_date(value) -> date:
        if value is None or value == "":
            raise CreateAccountValidationError(
                "Date of Birth is required."
            )

        if isinstance(value, datetime):
            raise CreateAccountValidationError(
                "dateOfBirth must use YYYY-MM-DD."
            )

        if isinstance(value, date):
            return value

        if not isinstance(value, str):
            raise CreateAccountValidationError(
                "dateOfBirth must use YYYY-MM-DD."
            )

        if not re.fullmatch(
            r"\d{4}-\d{2}-\d{2}",
            value,
        ):
            raise CreateAccountValidationError(
                "dateOfBirth must use YYYY-MM-DD."
            )

        try:
            return date.fromisoformat(value)

        except ValueError as exc:
            raise CreateAccountValidationError(
                "Invalid Date of Birth."
            ) from exc

    # =========================================
    # EMAIL
    # =========================================

    @staticmethod
    def _validate_email(email: str) -> str:
        if not re.fullmatch(
            r"[^@\s]+@[^@\s]+\.[^@\s]+",
            email,
        ):
            raise CreateAccountValidationError(
                "Invalid Email."
            )

        return email

    # =========================================
    # INITIAL CREDENTIALS
    # =========================================

    @staticmethod
    def _generate_initial_password() -> str:
        uppercase = string.ascii_uppercase
        lowercase = string.ascii_lowercase
        digits = string.digits
        symbols = "!@#$%&*-_"

        characters = [
            secrets.choice(uppercase),
            secrets.choice(lowercase),
            secrets.choice(digits),
            secrets.choice(symbols),
        ]

        alphabet = (
            uppercase + lowercase + digits + symbols
        )

        for _ in range(16):
            characters.append(
                secrets.choice(alphabet)
            )

        secrets.SystemRandom().shuffle(characters)

        return "".join(characters)

    # =========================================
    # VALIDATE INPUT
    # =========================================

    @classmethod
    def _validate_payload(cls, payload: dict) -> dict:
        if not isinstance(payload, dict):
            raise CreateAccountValidationError(
                "Invalid account data."
            )

        account_type = payload.get("accountType")

        if account_type not in ("Student", "Lecturer"):
            raise CreateAccountValidationError(
                "Account type must be Student or Lecturer."
            )

        allowed_fields = (
            cls.STUDENT_FIELDS
            if account_type == "Student"
            else cls.LECTURER_FIELDS
        )

        unsupported = set(payload) - allowed_fields

        if unsupported:
            raise CreateAccountValidationError(
                "Unsupported fields: "
                + ", ".join(sorted(unsupported))
            )

        username = cls._required_text(
            payload.get("username"),
            "Username",
            50,
        )

        citizen_id = cls._required_text(
            payload.get("citizenId"),
            "Citizen ID",
            12,
        )

        full_name = cls._required_text(
            payload.get("fullName"),
            "Full Name",
            200,
        )

        # All fields below are mandatory according
        # to the Group 05 account creation rules.
        date_of_birth = cls._parse_date(
            payload.get("dateOfBirth")
        )

        email = cls._required_text(
            payload.get("email"),
            "Email",
            100,
        )
        email = cls._validate_email(email)

        phone_number = cls._required_text(
            payload.get("phoneNumber"),
            "Phone Number",
            15,
        )

        gender = cls._required_text(
            payload.get("gender"),
            "Gender",
            20,
        )

        validated = {
            "account_type": account_type,
            "username": username,
            "citizen_id": citizen_id,
            "full_name": full_name,
            "date_of_birth": date_of_birth,
            "email": email,
            "phone_number": phone_number,
            "gender": gender,
        }

        if account_type == "Student":
            validated["major_id"] = (
                cls._required_text(
                    payload.get("majorId"),
                    "Major ID",
                    10,
                )
            )

            validated["academic_status"] = (
                cls._required_text(
                    payload.get("academicStatus"),
                    "Academic Status",
                    60,
                )
            )

        else:
            validated["faculty_id"] = (
                cls._required_text(
                    payload.get("facultyId"),
                    "Faculty ID",
                    10,
                )
            )

        return validated

    # =========================================
    # FACULTY / MAJOR OPTIONS
    # =========================================

    def list_faculties(self) -> list[dict]:
        return self._repo.list_faculties()

    def list_majors(self) -> list[dict]:
        return self._repo.list_majors()

    # =========================================
    # CREATE ACCOUNT
    # =========================================

    def create_record(self, payload: dict) -> dict:
        validated = self._validate_payload(payload)

        initial_password = (
            self._generate_initial_password()
        )

        password_hash = generate_password_hash(
            initial_password,
            method="pbkdf2:sha256:600000",
        )

        # Repository generates IDs and inserts Users
        # with Students/Lecturers in one transaction.
        account = self._repo.create_account(
            **validated,
            password_hash=password_hash,
        )

        # Internal handoff to the notification layer.
        # Never log or expose the initial password
        # through a normal public API response.
        return {
            "account": account,
            "initialCredentials": {
                "username": validated["username"],
                "initialPassword": initial_password,
            },
        }
