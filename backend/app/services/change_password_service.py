
"""Change Password Service - Student Management System Group 05."""

import re

from werkzeug.security import (
    check_password_hash,
    generate_password_hash,
)


class PasswordChangeError(ValueError):
    """Invalid password change request."""


class IncorrectCurrentPasswordError(PasswordChangeError):
    """The current password is incorrect."""


class PasswordUpdateConflictError(PasswordChangeError):
    """The password changed during the request."""


class ChangePasswordService:
    def __init__(self, repository):
        self._repository = repository

    @staticmethod
    def _validate_new_password(password):
        if not isinstance(password, str):
            raise PasswordChangeError(
                "New password is required."
            )

        if not 8 <= len(password) <= 128:
            raise PasswordChangeError(
                "Password must contain 8 to 128 characters."
            )

        if not (
            re.search(r"[A-Z]", password)
            and re.search(r"[a-z]", password)
            and re.search(r"[0-9]", password)
            and re.search(r"[^A-Za-z0-9]", password)
        ):
            raise PasswordChangeError(
                "Password must include uppercase, lowercase, "
                "number and special characters."
            )

    def change_password(
        self,
        user_id,
        current_password,
        new_password,
        confirm_password,
    ):
        if not isinstance(user_id, str) or not user_id.strip():
            raise PasswordChangeError(
                "Invalid authenticated user."
            )

        if not isinstance(current_password, str) or not current_password:
            raise PasswordChangeError(
                "Current password is required."
            )

        if new_password != confirm_password:
            raise PasswordChangeError(
                "Password confirmation does not match."
            )

        self._validate_new_password(new_password)

        # Retrieve existing hash from the Users table.
        current_hash = self._repository.get_password_hash(
            user_id.strip()
        )

        # Do not reveal whether the account exists.
        if not current_hash or not check_password_hash(
            current_hash,
            current_password,
        ):
            raise IncorrectCurrentPasswordError(
                "Current password is incorrect."
            )

        if check_password_hash(current_hash, new_password):
            raise PasswordChangeError(
                "New password must differ from current password."
            )

        # Compatible with the project's PBKDF2 hashes.
        new_hash = generate_password_hash(
            new_password,
            method="pbkdf2:sha256:600000",
        )

        # Repository must update with an atomic conditional
        # SQL statement and commit only on success.
        updated = (
            self._repository.replace_password_hash_if_unchanged(
                user_id=user_id.strip(),
                old_hash=current_hash,
                new_hash=new_hash,
            )
        )

        if not updated:
            raise PasswordUpdateConflictError(
                "Password was changed by another request. Try again."
            )

        return {
            "message": "Password changed successfully."
        }
