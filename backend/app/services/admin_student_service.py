
"""Administrator Student Management application service."""

from dataclasses import asdict
from datetime import date, datetime

from app.repositories.student_repository import (
    StudentRecord,
    StudentRepository,
    StudentDuplicateCitizenIdError,
    StudentDataIntegrityError,
)


class StudentNotFoundError(LookupError):
    """Requested student record does not exist."""


class StudentValidationError(ValueError):
    """Student input does not satisfy validation rules."""


def _serialize(record: StudentRecord) -> dict:
    data = asdict(record)

    data["dateOfBirth"] = (
        record.dateOfBirth.isoformat()
        if record.dateOfBirth
        else None
    )

    return data


class AdminStudentService:

    EDITABLE_FIELDS = {
        "citizenId",
        "fullName",
        "dateOfBirth",
        "email",
        "gender",
        "phoneNumber",
        "majorId",
        "academicStatus",
    }

    def __init__(
        self,
        repository: StudentRepository | None = None,
    ):
        self._repo = (
            repository
            if repository is not None
            else StudentRepository()
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
            raise StudentValidationError(
                f"{field_name} is required."
            )

        value = value.strip()

        if not value:
            raise StudentValidationError(
                f"{field_name} is required."
            )

        if len(value) > max_length:
            raise StudentValidationError(
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
            raise StudentValidationError(
                f"{field_name} must be a string."
            )

        value = value.strip()

        if not value:
            return None

        if len(value) > max_length:
            raise StudentValidationError(
                f"{field_name} must not exceed "
                f"{max_length} characters."
            )

        return value

    @staticmethod
    def _parse_date(value) -> date | None:

        if value is None or value == "":
            return None

        if isinstance(value, datetime):
            raise StudentValidationError(
                "dateOfBirth must use YYYY-MM-DD format."
            )

        if isinstance(value, date):
            return value

        if not isinstance(value, str):
            raise StudentValidationError(
                "dateOfBirth must use YYYY-MM-DD format."
            )

        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise StudentValidationError(
                "Invalid dateOfBirth. Expected YYYY-MM-DD."
            ) from exc

    # =========================================
    # VIEW STUDENT LIST
    # =========================================

    def list_records(
        self,
        *,
        limit: int = 10,
        offset: int = 0,
        search: str = "",
    ) -> dict:

        students = self._repo.list_students(
            limit=limit,
            offset=offset,
            search=search,
        )

        total = self._repo.count_students(
            search=search
        )

        return {
            "items": [
                _serialize(student)
                for student in students
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    # =========================================
    # VIEW STUDENT DETAILS
    # =========================================

    def get_record(
        self,
        student_id: str,
    ) -> dict:

        record = self._repo.get_student_by_id(
            student_id
        )

        if record is None:
            raise StudentNotFoundError(
                "Student record not found."
            )

        return _serialize(record)

    # =========================================
    # UPDATE STUDENT RECORD
    # =========================================

    def update_record(
        self,
        student_id: str,
        payload: dict,
    ) -> dict:

        if not isinstance(payload, dict):
            raise StudentValidationError(
                "Invalid student data."
            )

        # Reject protected or unsupported properties.
        unsupported = set(payload.keys()) - self.EDITABLE_FIELDS

        if unsupported:
            raise StudentValidationError(
                "Unsupported or non-editable fields: "
                + ", ".join(sorted(unsupported))
            )

        required_fields = {
            "citizenId",
            "fullName",
            "majorId",
            "academicStatus",
        }

        missing = required_fields - set(payload.keys())

        if missing:
            raise StudentValidationError(
                "Missing required fields: "
                + ", ".join(sorted(missing))
            )

        # Validate according to the actual SQL Server schema.
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

        major_id = self._required_text(
            payload.get("majorId"),
            "Major ID",
            10,
        )

        academic_status = self._required_text(
            payload.get("academicStatus"),
            "Academic status",
            60,
        )

        date_of_birth = self._parse_date(
            payload.get("dateOfBirth")
        )

        email = self._optional_text(
            payload.get("email"),
            "Email",
            100,
        )

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

        # Execute the update through Repository.
        updated = self._repo.update_student(
            student_id=student_id,
            citizen_id=citizen_id,
            full_name=full_name,
            date_of_birth=date_of_birth,
            email=email,
            gender=gender,
            phone_number=phone_number,
            major_id=major_id,
            academic_status=academic_status,
        )

        if updated is None:
            raise StudentNotFoundError(
                "Student record not found."
            )

        return _serialize(updated)

    # =========================================
    # DELETE STUDENT RECORD
    # =========================================

    def delete_record(
        self,
        student_id: str,
    ) -> bool:

        deleted = self._repo.delete_student(
            student_id
        )

        if not deleted:
            raise StudentNotFoundError(
                "Student record not found."
            )

        return True
