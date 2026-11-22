
"""Business rules for Administrator Class Section Management.

Use Cases 35-39:
- Manage Class Sections
- Create Class Sections
- View Class Sections
- Update Class Sections
- Delete Class Sections

Lecturer assignment is handled separately by Use Case 40.
"""

import re
from datetime import time

from app.repositories.admin_class_section_repository import (
    AdminClassSectionRepository,
)


# ============================================================
# EXPECTED REQUEST FIELDS
# ============================================================

CREATE_FIELDS = frozenset({
    "classCode",
    "courseId",
    "semesterId",
    "maxCapacity",
    "room",
    "dayOfWeek",
    "startTime",
    "endTime",
})

UPDATE_FIELDS = frozenset({
    "maxCapacity",
    "room",
    "dayOfWeek",
    "startTime",
    "endTime",
})


# ============================================================
# SERVICE
# ============================================================

class AdminClassSectionService:
    """Validate Class Section requests and apply business rules."""

    def __init__(self, repository=None):
        self._repository = (
            repository
            if repository is not None
            else AdminClassSectionRepository()
        )

    # ========================================================
    # 1. VALIDATE CLASS SECTION ID
    # ========================================================

    @staticmethod
    def _validate_section_id(value):
        if (
            not isinstance(value, str)
            or not re.fullmatch(
                r"CLS[0-9]{7}",
                value,
            )
        ):
            raise ValueError(
                "Invalid Class Section ID."
            )

        return value

    # ========================================================
    # 2. VALIDATE COURSE ID
    # ========================================================

    @staticmethod
    def _validate_course_id(value):
        if (
            not isinstance(value, str)
            or not re.fullmatch(
                r"CRS[0-9]{7}",
                value,
            )
        ):
            raise ValueError(
                "Invalid Course ID."
            )

        return value

    # ========================================================
    # 3. VALIDATE SEMESTER ID
    # ========================================================

    @staticmethod
    def _validate_semester_id(value):
        if (
            not isinstance(value, str)
            or not re.fullmatch(
                r"SEM[0-9]{7}",
                value,
            )
        ):
            raise ValueError(
                "Invalid Semester ID."
            )

        return value

    # ========================================================
    # 4. VALIDATE CLASS CODE
    # ========================================================

    @staticmethod
    def _validate_class_code(value):
        if not isinstance(value, str):
            raise ValueError(
                "Class Code is required."
            )

        code = value.strip().upper()

        if not re.fullmatch(
            r"[A-Z0-9][A-Z0-9._-]{0,19}",
            code,
        ):
            raise ValueError(
                "Class Code must contain 1-20 "
                "letters, numbers, dots, "
                "underscores or hyphens."
            )

        return code

    # ========================================================
    # 5. VALIDATE MAXIMUM CAPACITY
    # ========================================================

    @staticmethod
    def _validate_capacity(value):
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or value <= 0
            or value > 2147483647
        ):
            raise ValueError(
                "Maximum Capacity must be "
                "a positive integer."
            )

        return value

    # ========================================================
    # 6. VALIDATE ROOM
    # ========================================================

    @staticmethod
    def _validate_room(value):
        if value is None:
            return None

        if not isinstance(value, str):
            raise ValueError(
                "Invalid Room."
            )

        room = value.strip()

        if not room:
            return None

        if len(room) > 30:
            raise ValueError(
                "Room must not exceed "
                "30 characters."
            )

        return room

    # ========================================================
    # 7. VALIDATE DAY OF WEEK
    # ========================================================

    @staticmethod
    def _validate_day_of_week(value):
        if value is None:
            return None

        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or not 1 <= value <= 7
        ):
            raise ValueError(
                "Day of Week must be "
                "an integer from 1 to 7."
            )

        return value

    # ========================================================
    # 8. VALIDATE TIME
    # ========================================================

    @staticmethod
    def _validate_time(value, label):
        if value is None:
            return None

        if isinstance(value, time):
            return value

        if not isinstance(value, str):
            raise ValueError(
                f"Invalid {label}."
            )

        raw = value.strip()

        if not raw:
            return None

        if not re.fullmatch(
            r"[0-9]{2}:[0-9]{2}"
            r"(?::[0-9]{2})?",
            raw,
        ):
            raise ValueError(
                f"{label} must use "
                "HH:MM or HH:MM:SS."
            )

        try:
            return time.fromisoformat(raw)

        except ValueError as exc:
            raise ValueError(
                f"Invalid {label}."
            ) from exc

    # ========================================================
    # 9. VALIDATE ROOM AND SCHEDULE
    # ========================================================

    @classmethod
    def _validate_schedule(
        cls,
        data,
        required,
    ):
        room = cls._validate_room(
            data["room"]
        )

        day = cls._validate_day_of_week(
            data["dayOfWeek"]
        )

        start = cls._validate_time(
            data["startTime"],
            "Start Time",
        )

        end = cls._validate_time(
            data["endTime"],
            "End Time",
        )

        components = (
            room,
            day,
            start,
            end,
        )

        has_any = any(
            item is not None
            for item in components
        )

        has_all = all(
            item is not None
            for item in components
        )

        # New sections require a complete schedule.
        if required and not has_all:
            raise ValueError(
                "Room, Day of Week, Start Time "
                "and End Time are required."
            )

        # For existing sections, allow a completely
        # unscheduled state because the SQL columns
        # are nullable. Partial schedules are rejected.
        if has_any and not has_all:
            raise ValueError(
                "Room and Class Schedule "
                "must be provided together."
            )

        if has_all and end <= start:
            raise ValueError(
                "End Time must be after Start Time."
            )

        return {
            "room": room,
            "dayOfWeek": day,
            "startTime": start,
            "endTime": end,
        }

    # ========================================================
    # 10. VALIDATE CREATE PAYLOAD
    # ========================================================

    @classmethod
    def _validate_create(cls, data):
        if (
            not isinstance(data, dict)
            or set(data.keys()) != CREATE_FIELDS
        ):
            raise ValueError(
                "Invalid Class Section creation fields."
            )

        schedule = cls._validate_schedule(
            data,
            required=True,
        )

        return {
            "classCode": cls._validate_class_code(
                data["classCode"]
            ),
            "courseId": cls._validate_course_id(
                data["courseId"]
            ),
            "semesterId": cls._validate_semester_id(
                data["semesterId"]
            ),
            "maxCapacity": cls._validate_capacity(
                data["maxCapacity"]
            ),
            **schedule,
        }

    # ========================================================
    # 11. VALIDATE UPDATE PAYLOAD
    # ========================================================

    @classmethod
    def _validate_update(cls, data):
        if (
            not isinstance(data, dict)
            or set(data.keys()) != UPDATE_FIELDS
        ):
            raise ValueError(
                "Only Maximum Capacity, Room "
                "and Class Schedule can be updated."
            )

        schedule = cls._validate_schedule(
            data,
            required=False,
        )

        return {
            "maxCapacity": cls._validate_capacity(
                data["maxCapacity"]
            ),
            **schedule,
        }

    # ========================================================
    # 12. LIST CLASS SECTIONS
    # ========================================================

    def list_sections(self, semester_id=None):
        if semester_id is not None:
            semester_id = self._validate_semester_id(
                semester_id
            )

        return self._repository.list_sections(
            semester_id
        )

    # ========================================================
    # 13. GET CLASS SECTION DETAILS
    # ========================================================

    def get_section(self, section_id):
        section_id = self._validate_section_id(
            section_id
        )

        return self._repository.get_section(
            section_id
        )

    # ========================================================
    # 14. LIST AVAILABLE SEMESTERS
    # ========================================================

    def list_semesters(self):
        return self._repository.list_semesters()

    # ========================================================
    # 15. LIST AVAILABLE COURSES
    # ========================================================

    def list_courses(self):
        return self._repository.list_courses()

    # ========================================================
    # 16. CREATE CLASS SECTION
    # ========================================================

    def create_section(self, data):
        fields = self._validate_create(
            data
        )

        return self._repository.create_section(
            fields
        )

    # ========================================================
    # 17. UPDATE CLASS SECTION
    # ========================================================

    def update_section(
        self,
        section_id,
        data,
    ):
        section_id = self._validate_section_id(
            section_id
        )

        fields = self._validate_update(
            data
        )

        return self._repository.update_section(
            section_id,
            fields,
        )

    # ========================================================
    # 18. DELETE CLASS SECTION
    # ========================================================

    def delete_section(self, section_id):
        section_id = self._validate_section_id(
            section_id
        )

        return self._repository.delete_section(
            section_id
        )
