
"""Administrator Lecturer Management Service.

Student Management System - Group 05.

Business logic for:
- View lecturer records
- Search and paginate lecturers
- View lecturer details
- Retrieve faculty options
- Update lecturer profiles
- Delete lecturer profiles

No SQL statements are written in this service.
"""

from dataclasses import asdict
from datetime import date, datetime
import re

from app.repositories.admin_lecturer_repository import (
    AdminLecturerRepository,
    LecturerRecord,
)


class LecturerNotFoundError(LookupError):
    """Requested lecturer record does not exist."""


class LecturerValidationError(ValueError):
    """Invalid lecturer management input."""


def _serialize(record: LecturerRecord) -> dict:
    """Convert the LecturerRecord DTO to an API dictionary."""

    data = asdict(record)

    data["dateOfBirth"] = (
        record.dateOfBirth.isoformat()
        if record.dateOfBirth is not None
        else None
    )

    return data


class AdminLecturerService:
    """Business logic for Administrator lecturer management."""

    EDITABLE_FIELDS = {
        "citizenId",
        "fullName",
        "dateOfBirth",
        "email",
        "gender",
        "phoneNumber",
        "facultyId",
    }

    REQUIRED_FIELDS = {
        "citizenId",
        "fullName",
        "facultyId",
    }

    def __init__(
        self,
        repository: AdminLecturerRepository | None = None,
    ):
        self._repo = (
            repository
            if repository is not None
            else AdminLecturerRepository()
        )

    # =========================================
    # VALIDATION HELPERS
    # =========================================

    @staticmethod
    def _required_text(
        value,
        field_name: str,
        max_length: int,
    ) -> str:

        if not isinstance(value, str):
            raise LecturerValidationError(
                f"{field_name} is required."
            )

        value = value.strip()

        if not value:
            raise LecturerValidationError(
                f"{field_name} is required."
            )

        if len(value) > max_length:
            raise LecturerValidationError(
                f"{field_name} must not exceed "
                f"{max_length} characters."
            )

        return value

    @staticmethod
    def _optional_text(
        value,
        field_name: str,
        max_length: int,
    ) -> str | None:

        if value is None or value == "":
            return None

        if not isinstance(value, str):
            raise LecturerValidationError(
                f"{field_name} must be a string."
            )

        value = value.strip()

        if not value:
            return None

        if len(value) > max_length:
            raise LecturerValidationError(
                f"{field_name} must not exceed "
                f"{max_length} characters."
            )

        return value

    @staticmethod
    def _parse_date(value) -> date | None:

        if value is None or value == "":
            return None

        if isinstance(value, datetime):
            raise LecturerValidationError(
                "dateOfBirth must use YYYY-MM-DD format."
            )

        if isinstance(value, date):
            return value

        if not isinstance(value, str):
            raise LecturerValidationError(
                "dateOfBirth must use YYYY-MM-DD format."
            )

        try:
            return date.fromisoformat(value)

        except ValueError as exc:
            raise LecturerValidationError(
                "Invalid dateOfBirth. Expected YYYY-MM-DD."
            ) from exc

    @staticmethod
    def _validate_email(value: str | None) -> str | None:

        if value is None:
            return None

        if not re.fullmatch(
            r"[^@\s]+@[^@\s]+\.[^@\s]+",
            value,
        ):
            raise LecturerValidationError(
                "Invalid email address."
            )

        return value

    @staticmethod
    def _validate_lecturer_id(value) -> str:

        if (
            not isinstance(value, str)
            or not value.strip()
            or len(value.strip()) > 10
        ):
            raise LecturerValidationError(
                "Invalid Lecturer ID."
            )

        return value.strip()

    # =========================================
    # VIEW LECTURER LIST
    # =========================================

    def list_records(
        self,
        *,
        limit: int = 10,
        offset: int = 0,
        search: str = "",
    ) -> dict:

        if type(limit) is not int or not 1 <= limit <= 100:
            raise LecturerValidationError(
                "limit must be an integer between 1 and 100."
            )

        if type(offset) is not int or offset < 0:
            raise LecturerValidationError(
                "offset must be a non-negative integer."
            )

        if (
            not isinstance(search, str)
            or len(search.strip()) > 100
        ):
            raise LecturerValidationError(
                "search must be a string up to 100 characters."
            )

        search = search.strip()

        lecturers = self._repo.list_lecturers(
            limit=limit,
            offset=offset,
            search=search,
        )

        total = self._repo.count_lecturers(
            search=search
        )

        return {
            "items": [
                _serialize(lecturer)
                for lecturer in lecturers
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    # =========================================
    # VIEW LECTURER DETAILS
    # =========================================

    def get_record(
        self,
        lecturer_id: str,
    ) -> dict:

        lecturer_id = self._validate_lecturer_id(
            lecturer_id
        )

        record = self._repo.get_lecturer_by_id(
            lecturer_id
        )

        if record is None:
            raise LecturerNotFoundError(
                "Lecturer record not found."
            )

        return _serialize(record)

    # =========================================
    # LIST FACULTY OPTIONS
    # =========================================

    def list_faculty_options(self) -> list[dict]:
        return self._repo.list_faculty_options()

    # =========================================
    # UPDATE LECTURER PROFILE
    # =========================================

    def update_record(
        self,
        lecturer_id: str,
        payload: dict,
    ) -> dict:

        lecturer_id = self._validate_lecturer_id(
            lecturer_id
        )

        if not isinstance(payload, dict):
            raise LecturerValidationError(
                "Invalid lecturer data."
            )

        unsupported = (
            set(payload.keys())
            - self.EDITABLE_FIELDS
        )

        if unsupported:
            raise LecturerValidationError(
                "Unsupported or non-editable fields: "
                + ", ".join(sorted(unsupported))
            )

        missing = (
            self.REQUIRED_FIELDS
            - set(payload.keys())
        )

        if missing:
            raise LecturerValidationError(
                "Missing required fields: "
                + ", ".join(sorted(missing))
            )

        # ---------------------------------
        # REQUIRED INFORMATION
        # ---------------------------------

        citizen_id = self._required_text(
            payload.get("citizenId"),
            "Citizen ID",
            12,
        )

        full_name = self._required_text(
            payload.get("fullName"),
            "Full name",
            200,
        )

        faculty_id = self._required_text(
            payload.get("facultyId"),
            "Faculty ID",
            10,
        )

        # ---------------------------------
        # OPTIONAL INFORMATION
        # ---------------------------------

        date_of_birth = self._parse_date(
            payload.get("dateOfBirth")
        )

        email = self._optional_text(
            payload.get("email"),
            "Email",
            100,
        )

        email = self._validate_email(email)

        gender = self._optional_text(
            payload.get("gender"),
            "Gender",
            20,
        )

        phone_number = self._optional_text(
            payload.get("phoneNumber"),
            "Phone number",
            15,
        )

        # ---------------------------------
        # DATABASE OPERATION
        # ---------------------------------

        updated = self._repo.update_lecturer(
            lecturer_id=lecturer_id,
            citizen_id=citizen_id,
            full_name=full_name,
            date_of_birth=date_of_birth,
            email=email,
            gender=gender,
            phone_number=phone_number,
            faculty_id=faculty_id,
        )

        if updated is None:
            raise LecturerNotFoundError(
                "Lecturer record not found."
            )

        return _serialize(updated)

    # =========================================
    # DELETE LECTURER PROFILE
    # =========================================

    def delete_record(
        self,
        lecturer_id: str,
    ) -> bool:

        lecturer_id = self._validate_lecturer_id(
            lecturer_id
        )

        deleted = self._repo.delete_lecturer(
            lecturer_id
        )

        if not deleted:
            raise LecturerNotFoundError(
                "Lecturer record not found."
            )

        return True
