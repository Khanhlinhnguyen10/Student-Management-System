
"""Lecturer Gradebook business rules."""

import re

from app.repositories.lecturer_gradebook_repository import (
    LecturerGradebookRepository,
)
from app.validators.grade_validator import GradeValidator


MARK_FIELDS = (
    "midtermMark",
    "assignmentMark",
    "attendanceMark",
    "finalExamMark",
)


class LecturerGradebookService:
    def __init__(self, repository=None):
        self._repository = (
            repository
            if repository is not None
            else LecturerGradebookRepository()
        )

    @staticmethod
    def _validate_id(value, limit, label):
        if (
            not isinstance(value, str)
            or not value.strip()
            or len(value.strip()) > limit
        ):
            raise ValueError(f"Invalid {label}.")

        return value.strip()

    @staticmethod
    def _validate_marks(data, required=False):
        if not isinstance(data, dict):
            raise ValueError("JSON object required.")

        if set(data.keys()) != set(MARK_FIELDS):
            raise ValueError(
                "Exactly four grade components are required."
            )

        return {
            field: GradeValidator.validate_mark(
                data[field],
                field,
                required=required,
            )
            for field in MARK_FIELDS
        }

    def get_section_gradebook(self, user_id, section_id):
        user_id = self._validate_id(
            user_id, 12, "Lecturer session"
        )
        section_id = self._validate_id(
            section_id, 10, "class section ID"
        )

        return self._repository.get_section_gradebook(
            user_id, section_id
        )

    def save_draft(
        self,
        user_id,
        section_id,
        enrollment_id,
        data,
    ):
        user_id = self._validate_id(
            user_id, 12, "Lecturer session"
        )
        section_id = self._validate_id(
            section_id, 10, "class section ID"
        )
        enrollment_id = self._validate_id(
            enrollment_id, 10, "enrollment ID"
        )

        # Draft permits missing marks (null).
        marks = self._validate_marks(
            data, required=False
        )

        return self._repository.save_draft(
            user_id,
            section_id,
            enrollment_id,
            marks,
        )

    def save_final(
        self,
        user_id,
        token_hash,
        section_id,
        enrollment_id,
        data,
    ):
        user_id = self._validate_id(
            user_id, 12, "Lecturer session"
        )
        section_id = self._validate_id(
            section_id, 10, "class section ID"
        )
        enrollment_id = self._validate_id(
            enrollment_id, 10, "enrollment ID"
        )

        if (
            not isinstance(token_hash, str)
            or not re.fullmatch(r"[0-9a-f]{64}", token_hash)
        ):
            raise ValueError("Invalid session token hash.")

        # Finalization requires all four numeric marks.
        marks = self._validate_marks(
            data, required=True
        )

        return self._repository.save_final(
            user_id,
            token_hash,
            section_id,
            enrollment_id,
            marks,
        )
