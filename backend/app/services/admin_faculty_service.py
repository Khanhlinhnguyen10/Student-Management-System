
"""Business validation for Administrator Faculty Management."""

import re

from app.repositories.admin_faculty_repository import (
    AdminFacultyRepository,
)


CREATE_FIELDS = frozenset({
    "facultyCode",
    "facultyName",
    "email",
    "phoneNumber",
})

UPDATE_FIELDS = frozenset({
    "facultyName",
    "email",
    "phoneNumber",
})


class AdminFacultyService:
    def __init__(self, repository=None):
        self._repository = (
            repository
            if repository is not None
            else AdminFacultyRepository()
        )

    # =========================================
    # VALIDATE FACULTY ID
    # =========================================

    @staticmethod
    def _validate_id(value):
        if (
            not isinstance(value, str)
            or not re.fullmatch(
                r"FAC[0-9]{7}",
                value,
            )
        ):
            raise ValueError(
                "Invalid Faculty ID."
            )

        return value

    # =========================================
    # VALIDATE FACULTY CODE
    # =========================================

    @staticmethod
    def _validate_code(value):
        if not isinstance(value, str):
            raise ValueError(
                "Faculty Code is required."
            )

        code = value.strip().upper()

        if not re.fullmatch(
            r"[A-Z0-9]{1,10}",
            code,
        ):
            raise ValueError(
                "Faculty Code must contain 1-10 "
                "letters or numbers."
            )

        return code

    # =========================================
    # VALIDATE FACULTY NAME
    # =========================================

    @staticmethod
    def _validate_name(value):
        if not isinstance(value, str):
            raise ValueError(
                "Faculty Name is required."
            )

        name = value.strip()

        if not name:
            raise ValueError(
                "Faculty Name is required."
            )

        if len(name) > 100:
            raise ValueError(
                "Faculty Name must not exceed "
                "100 characters."
            )

        return name

    # =========================================
    # VALIDATE EMAIL
    # =========================================

    @staticmethod
    def _validate_email(value):
        if not isinstance(value, str):
            raise ValueError(
                "Email is required."
            )

        email = value.strip().lower()

        if (
            not email
            or len(email) > 100
            or not re.fullmatch(
                r"[^@\s]+@[^@\s]+\.[^@\s]+",
                email,
            )
        ):
            raise ValueError(
                "Invalid faculty email."
            )

        return email

    # =========================================
    # VALIDATE PHONE NUMBER
    # =========================================

    @staticmethod
    def _validate_phone(value):
        if not isinstance(value, str):
            raise ValueError(
                "Phone Number is required."
            )

        phone = value.strip()

        if not re.fullmatch(
            r"\+?[0-9]{8,15}",
            phone,
        ):
            raise ValueError(
                "Phone Number must contain "
                "8-15 digits, optionally with +."
            )

        if len(phone) > 15:
            raise ValueError(
                "Phone Number must not exceed "
                "15 characters."
            )

        return phone

    # =========================================
    # VALIDATE CREATE PAYLOAD
    # =========================================

    @classmethod
    def _validate_create(cls, data):
        if (
            not isinstance(data, dict)
            or set(data.keys()) != CREATE_FIELDS
        ):
            raise ValueError(
                "Exactly Faculty Code, Faculty Name, "
                "Email and Phone Number are required."
            )

        return {
            "facultyCode": cls._validate_code(
                data["facultyCode"]
            ),
            "facultyName": cls._validate_name(
                data["facultyName"]
            ),
            "email": cls._validate_email(
                data["email"]
            ),
            "phoneNumber": cls._validate_phone(
                data["phoneNumber"]
            ),
        }

    # =========================================
    # VALIDATE UPDATE PAYLOAD
    # =========================================

    @classmethod
    def _validate_update(cls, data):
        if (
            not isinstance(data, dict)
            or set(data.keys()) != UPDATE_FIELDS
        ):
            raise ValueError(
                "Only Faculty Name, Email and "
                "Phone Number can be updated."
            )

        return {
            "facultyName": cls._validate_name(
                data["facultyName"]
            ),
            "email": cls._validate_email(
                data["email"]
            ),
            "phoneNumber": cls._validate_phone(
                data["phoneNumber"]
            ),
        }

    # =========================================
    # CRUD OPERATIONS
    # =========================================

    def list_faculties(self):
        return self._repository.list_faculties()

    def get_faculty(self, faculty_id):
        faculty_id = self._validate_id(
            faculty_id
        )

        return self._repository.get_faculty(
            faculty_id
        )

    def create_faculty(self, data):
        fields = self._validate_create(data)

        return self._repository.create_faculty(
            fields
        )

    def update_faculty(self, faculty_id, data):
        faculty_id = self._validate_id(
            faculty_id
        )

        fields = self._validate_update(
            data
        )

        return self._repository.update_faculty(
            faculty_id,
            fields,
        )

    def delete_faculty(self, faculty_id):
        faculty_id = self._validate_id(
            faculty_id
        )

        return self._repository.delete_faculty(
            faculty_id
        )
