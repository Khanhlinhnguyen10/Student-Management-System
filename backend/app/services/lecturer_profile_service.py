
import re

from app.repositories.lecturer_profile_repository import (
    LecturerProfileRepository,
)


class LecturerProfileService:
    def __init__(self, repository=None):
        self._repository = (
            repository
            if repository is not None
            else LecturerProfileRepository()
        )

    @staticmethod
    def _validate_user_id(user_id):
        if (
            not isinstance(user_id, str)
            or not user_id.strip()
            or len(user_id.strip()) > 12
        ):
            raise ValueError("Invalid lecturer session.")

        return user_id.strip()

    def get_profile(self, user_id):
        user_id = self._validate_user_id(user_id)
        return self._repository.get_profile(user_id)

    def update_contact(self, user_id, data):
        user_id = self._validate_user_id(user_id)

        if not isinstance(data, dict):
            raise ValueError("A JSON object is required.")

        # Reject attempts to change IDs, name, faculty,
        # or any field outside the approved contact fields.
        if set(data.keys()) != {"email", "phoneNumber"}:
            raise ValueError(
                "Only email and phoneNumber can be updated."
            )

        email = data["email"]
        phone_number = data["phoneNumber"]

        if email is not None:
            if not isinstance(email, str):
                raise ValueError("Invalid email.")

            email = email.strip() or None

        if phone_number is not None:
            if not isinstance(phone_number, str):
                raise ValueError("Invalid phone number.")

            phone_number = phone_number.strip() or None

        if email is not None:
            if len(email) > 100 or not email.isascii():
                raise ValueError("Invalid email.")

            if not re.fullmatch(
                r"[^@\s]+@[^@\s]+\.[^@\s]+",
                email,
            ):
                raise ValueError("Invalid email format.")

        if phone_number is not None:
            if (
                len(phone_number) > 15
                or not re.fullmatch(
                    r"\+?[0-9]{9,14}",
                    phone_number,
                )
            ):
                raise ValueError("Invalid phone number format.")

        return self._repository.update_contact(
            user_id,
            email,
            phone_number,
        )
