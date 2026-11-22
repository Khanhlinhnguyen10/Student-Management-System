
"""Validation and business rules for Administrator Semester Management."""

import re
from datetime import date

from app.repositories.admin_semester_repository import (
    AdminSemesterRepository,
)


FIELDS = frozenset({
    "semesterName",
    "academicYear",
    "startDate",
    "endDate",
})


class AdminSemesterService:
    def __init__(self, repository=None):
        self._repository = (
            repository
            if repository is not None
            else AdminSemesterRepository()
        )

    # =========================================
    # VALIDATE SEMESTER ID
    # =========================================

    @staticmethod
    def _validate_id(value):
        if (
            not isinstance(value, str)
            or not re.fullmatch(
                r"SEM\d{7}",
                value,
            )
        ):
            raise ValueError(
                "Invalid Semester ID."
            )

        return value

    # =========================================
    # VALIDATE SEMESTER FIELDS
    # =========================================

    @staticmethod
    def _validate_fields(data):
        if (
            not isinstance(data, dict)
            or set(data) != FIELDS
        ):
            raise ValueError(
                "Exactly Semester Name, "
                "Academic Year, Start Date "
                "and End Date are required."
            )

        # Semester Name
        name = data["semesterName"]

        if (
            not isinstance(name, str)
            or not name.strip()
        ):
            raise ValueError(
                "Semester Name is required."
            )

        name = name.strip()

        if len(name) > 50:
            raise ValueError(
                "Semester Name must not "
                "exceed 50 characters."
            )

        # Academic Year
        year = data["academicYear"]

        if (
            not isinstance(year, str)
            or not re.fullmatch(
                r"\d{4}-\d{4}",
                year,
            )
        ):
            raise ValueError(
                "Academic Year must use YYYY-YYYY."
            )

        first, second = map(
            int,
            year.split("-"),
        )

        if second != first + 1:
            raise ValueError(
                "Academic Year must span "
                "consecutive years."
            )

        # Start Date and End Date
        parsed = {}

        for key, label in (
            ("startDate", "Start Date"),
            ("endDate", "End Date"),
        ):
            raw = data[key]

            if (
                not isinstance(raw, str)
                or not re.fullmatch(
                    r"\d{4}-\d{2}-\d{2}",
                    raw,
                )
            ):
                raise ValueError(
                    f"{label} must use YYYY-MM-DD."
                )

            try:
                parsed[key] = date.fromisoformat(
                    raw
                )

            except ValueError as exc:
                raise ValueError(
                    f"{label} is invalid."
                ) from exc

        # End Date must be after Start Date.
        if (
            parsed["endDate"]
            <= parsed["startDate"]
        ):
            raise ValueError(
                "End Date must be after Start Date."
            )

        return {
            "semesterName": name,
            "academicYear": year,
            "startDate": parsed["startDate"],
            "endDate": parsed["endDate"],
        }

    # =========================================
    # BUSINESS OPERATIONS
    # =========================================

    def list_semesters(self):
        return self._repository.list_semesters()

    def get_semester(self, semester_id):
        semester_id = self._validate_id(
            semester_id
        )

        return self._repository.get_semester(
            semester_id
        )

    def create_semester(self, data):
        fields = self._validate_fields(data)

        return self._repository.create_semester(
            fields
        )

    def update_semester(
        self,
        semester_id,
        data,
    ):
        semester_id = self._validate_id(
            semester_id
        )

        fields = self._validate_fields(
            data
        )

        return self._repository.update_semester(
            semester_id,
            fields,
        )

    def delete_semester(self, semester_id):
        semester_id = self._validate_id(
            semester_id
        )

        return self._repository.delete_semester(
            semester_id
        )
