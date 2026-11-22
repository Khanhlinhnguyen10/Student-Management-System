
"""Business validation for Administrator Course Management."""

import re
from decimal import Decimal, InvalidOperation

from app.repositories.admin_course_repository import (
    AdminCourseRepository,
)


WEIGHT_FIELDS = (
    "midtermWeight",
    "assignmentWeight",
    "attendanceWeight",
    "finalExamWeight",
)

CREATE_FIELDS = frozenset({
    "facultyId",
    "courseCode",
    "courseName",
    "credits",
    "prerequisiteIds",
    *WEIGHT_FIELDS,
})

UPDATE_FIELDS = CREATE_FIELDS - {"courseCode"}

ID_PATTERN = re.compile(r"CRS[0-9]{7}")
FACULTY_PATTERN = re.compile(r"FAC[0-9]{7}")


class AdminCourseService:
    def __init__(self, repository=None):
        self._repository = (
            repository
            if repository is not None
            else AdminCourseRepository()
        )

    @staticmethod
    def _validate_id(value):
        if (
            not isinstance(value, str)
            or not ID_PATTERN.fullmatch(value)
        ):
            raise ValueError("Invalid Course ID.")

        return value

    @staticmethod
    def _validate_faculty_id(value):
        if (
            not isinstance(value, str)
            or not FACULTY_PATTERN.fullmatch(value)
        ):
            raise ValueError(
                "Invalid Managing Faculty."
            )

        return value

    @staticmethod
    def _validate_code(value):
        if not isinstance(value, str):
            raise ValueError(
                "Course Code is required."
            )

        code = value.strip().upper()

        if not re.fullmatch(
            r"[A-Z0-9]{1,10}",
            code,
        ):
            raise ValueError(
                "Course Code must contain "
                "1-10 letters or numbers."
            )

        return code

    @staticmethod
    def _validate_name(value):
        if not isinstance(value, str):
            raise ValueError(
                "Course Name is required."
            )

        name = value.strip()

        if not name:
            raise ValueError(
                "Course Name is required."
            )

        if len(name) > 100:
            raise ValueError(
                "Course Name must not exceed "
                "100 characters."
            )

        return name

    @staticmethod
    def _validate_credits(value):
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or not 1 <= value <= 255
        ):
            raise ValueError(
                "Credits must be a positive integer "
                "between 1 and 255."
            )

        return value

    @staticmethod
    def _validate_weight(value, label):
        if isinstance(value, bool):
            raise ValueError(
                f"Invalid {label}."
            )

        try:
            number = Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            raise ValueError(
                f"Invalid {label}."
            ) from None

        if (
            not number.is_finite()
            or number < 0
            or number > 100
            or number != number.quantize(
                Decimal("0.01")
            )
        ):
            raise ValueError(
                f"{label} must be between 0 and 100 "
                "with up to 2 decimal places."
            )

        return number

    @classmethod
    def _validate_weights(cls, data):
        weights = {
            field: cls._validate_weight(
                data[field],
                field,
            )
            for field in WEIGHT_FIELDS
        }

        if sum(weights.values()) != Decimal("100"):
            raise ValueError(
                "The four grading weights "
                "must total 100%."
            )

        return weights

    @classmethod
    def _validate_prerequisites(
        cls,
        value,
        course_id=None,
    ):
        if not isinstance(value, list):
            raise ValueError(
                "Prerequisites must be a list."
            )

        ids = []

        for item in value:
            identifier = cls._validate_id(item)

            if identifier in ids:
                raise ValueError(
                    "Duplicate prerequisite course."
                )

            if identifier == course_id:
                raise ValueError(
                    "A course cannot be its own "
                    "prerequisite."
                )

            ids.append(identifier)

        return ids

    @classmethod
    def _validate_fields(
        cls,
        data,
        creating,
        course_id=None,
    ):
        expected = (
            CREATE_FIELDS if creating
            else UPDATE_FIELDS
        )

        if (
            not isinstance(data, dict)
            or set(data) != expected
        ):
            raise ValueError(
                "Invalid course fields. "
                "Course Code cannot be changed."
            )

        weights = cls._validate_weights(data)

        fields = {
            "facultyId": cls._validate_faculty_id(
                data["facultyId"]
            ),
            "courseName": cls._validate_name(
                data["courseName"]
            ),
            "credits": cls._validate_credits(
                data["credits"]
            ),
            "prerequisiteIds": cls._validate_prerequisites(
                data["prerequisiteIds"],
                course_id,
            ),
            **weights,
        }

        if creating:
            fields["courseCode"] = cls._validate_code(
                data["courseCode"]
            )

        return fields

    def list_courses(self):
        return self._repository.list_courses()

    def get_course(self, course_id):
        course_id = self._validate_id(
            course_id
        )

        return self._repository.get_course(
            course_id
        )

    def create_course(self, data):
        fields = self._validate_fields(
            data,
            creating=True,
        )

        return self._repository.create_course(
            fields
        )

    def update_course(self, course_id, data):
        course_id = self._validate_id(
            course_id
        )

        fields = self._validate_fields(
            data,
            creating=False,
            course_id=course_id,
        )

        return self._repository.update_course(
            course_id,
            fields,
        )

    def delete_course(self, course_id):
        course_id = self._validate_id(
            course_id
        )

        return self._repository.delete_course(
            course_id
        )
