
"""Business logic for Student View Profile / Update Information."""

import re

from app.repositories.student_profile_repository import (
    StudentProfileRepository,
)


class StudentProfileNotFoundError(LookupError):
    """The authenticated user has no student profile."""


class StudentContactValidationError(ValueError):
    """Contact information is missing or invalid."""


class StudentProfileService:
    EDITABLE_FIELDS = frozenset({
        "email",
        "phoneNumber",
    })

    def __init__(
        self,
        repository: StudentProfileRepository | None = None,
    ):
        self._repo = (
            repository
            if repository is not None
            else StudentProfileRepository()
        )

    @staticmethod
    def _validate_user_id(user_id: str) -> str:
        if (
            not isinstance(user_id, str)
            or not user_id.strip()
            or len(user_id.strip()) > 12
        ):
            raise ValueError("Invalid authenticated user ID.")

        return user_id.strip()

    @staticmethod
    def _optional_string(
        value,
        *,
        field: str,
        max_length: int,
    ) -> str | None:
        if value is None:
            return None

        if not isinstance(value, str):
            raise StudentContactValidationError(
                f"{field} must be a string."
            )

        value = value.strip()

        if not value:
            return None

        if len(value) > max_length:
            raise StudentContactValidationError(
                f"{field} exceeds {max_length} characters."
            )

        return value

    @classmethod
    def _validate_email(cls, value) -> str | None:
        email = cls._optional_string(
            value,
            field="email",
            max_length=100,
        )

        if email is None:
            return None

        if not re.fullmatch(
            r"[^@\s]+@[^@\s]+\.[^@\s]+",
            email,
        ):
            raise StudentContactValidationError(
                "Invalid email format."
            )

        return email

    @classmethod
    def _validate_phone(cls, value) -> str | None:
        phone = cls._optional_string(
            value,
            field="phoneNumber",
            max_length=15,
        )

        if phone is None:
            return None

        if not re.fullmatch(r"\+?[0-9]{9,14}", phone):
            raise StudentContactValidationError(
                "Invalid phoneNumber format."
            )

        return phone

    def view_profile(self, user_id: str) -> dict:
        user_id = self._validate_user_id(user_id)

        profile = self._repo.get_profile(user_id)

        if profile is None:
            raise StudentProfileNotFoundError(
                "Student profile not found."
            )

        return profile

    def update_information(
        self,
        user_id: str,
        payload: dict,
    ) -> dict:
        user_id = self._validate_user_id(user_id)

        if not isinstance(payload, dict):
            raise StudentContactValidationError(
                "Invalid contact information."
            )

        unsupported = (
            set(payload.keys()) - self.EDITABLE_FIELDS
        )

        if unsupported:
            raise StudentContactValidationError(
                "Non-editable fields: "
                + ", ".join(sorted(unsupported))
            )

        missing = self.EDITABLE_FIELDS - set(payload.keys())

        if missing:
            raise StudentContactValidationError(
                "Missing fields: "
                + ", ".join(sorted(missing))
            )

        email = self._validate_email(
            payload["email"]
        )

        phone_number = self._validate_phone(
            payload["phoneNumber"]
        )

        profile = self._repo.update_contact(
            user_id,
            email=email,
            phone_number=phone_number,
        )

        if profile is None:
            raise StudentProfileNotFoundError(
                "Student profile not found."
            )

        return profile
