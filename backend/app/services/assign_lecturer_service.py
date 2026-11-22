
"""Assign Lecturer Service - Student Management System Group 05.

Use Case 40 - Assign Lecturer to Class Sections.

Responsibilities:
- Validate semester and assignment identifiers.
- Reject missing or unsupported input fields.
- Delegate database access and schedule checks to Repository.
- Preserve Repository exceptions for Controller error handling.

No direct SQL statements.
No database schema modifications.
"""

from app.repositories.assign_lecturer_repository import (
    AssignLecturerRepository,
)


class AssignLecturerValidationError(ValueError):
    """Invalid input for lecturer assignment."""


class AssignLecturerService:
    """Business-facing service for Assign Lecturer."""

    ASSIGNMENT_FIELDS = {
        "classSectionId",
        "lecturerId",
    }

    def __init__(
        self,
        repository: AssignLecturerRepository | None = None,
    ):
        self._repo = (
            repository
            if repository is not None
            else AssignLecturerRepository()
        )

    # =========================================
    # VALIDATION
    # =========================================

    @staticmethod
    def _required_identifier(
        value,
        field_name: str,
    ) -> str:
        if not isinstance(value, str):
            raise AssignLecturerValidationError(
                f"{field_name} is required."
            )

        value = value.strip()

        if not value:
            raise AssignLecturerValidationError(
                f"{field_name} is required."
            )

        # SQL FINAL uses varchar(10) for
        # Semester, Class Section and Lecturer IDs.
        if len(value) > 10:
            raise AssignLecturerValidationError(
                f"{field_name} must not exceed 10 characters."
            )

        return value

    # =========================================
    # LIST SEMESTERS
    # =========================================

    def list_semesters(self) -> list[dict]:
        return self._repo.list_semesters()

    # =========================================
    # LIST CLASS SECTIONS
    # =========================================

    def list_sections(
        self,
        semester_id: str,
    ) -> list[dict]:
        semester_id = self._required_identifier(
            semester_id,
            "Semester ID",
        )

        return self._repo.list_sections(
            semester_id
        )

    # =========================================
    # LIST LECTURERS
    # =========================================

    def list_lecturers(self) -> list[dict]:
        return self._repo.list_lecturers()

    # =========================================
    # ASSIGN LECTURER
    # =========================================

    def assign_record(self, payload: dict) -> dict:
        """Validate assignment and delegate atomic update.

        Expected JSON:
        {
            "classSectionId": "...",
            "lecturerId": "..."
        }

        Actual conflict detection and SQL transaction
        are performed in AssignLecturerRepository.
        """

        if not isinstance(payload, dict):
            raise AssignLecturerValidationError(
                "Invalid assignment data."
            )

        unsupported_fields = (
            set(payload.keys())
            - self.ASSIGNMENT_FIELDS
        )

        if unsupported_fields:
            raise AssignLecturerValidationError(
                "Unsupported fields: "
                + ", ".join(
                    sorted(unsupported_fields)
                )
            )

        class_section_id = (
            self._required_identifier(
                payload.get("classSectionId"),
                "Class Section ID",
            )
        )

        lecturer_id = (
            self._required_identifier(
                payload.get("lecturerId"),
                "Lecturer ID",
            )
        )

        # Repository performs:
        # 1. SQL transaction lock
        # 2. Section existence check
        # 3. Lecturer existence check
        # 4. Schedule conflict check
        # 5. UPDATE dbo.ClassSections
        # 6. Commit or rollback
        return self._repo.assign_lecturer(
            class_section_id=class_section_id,
            lecturer_id=lecturer_id,
        )
