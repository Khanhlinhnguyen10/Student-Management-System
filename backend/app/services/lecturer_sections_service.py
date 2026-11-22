
"""Business service for lecturer assigned sections."""

from app.repositories.lecturer_sections_repository import (
    LecturerSectionsRepository,
)


class LecturerSectionsService:

    def __init__(self, repository=None):
        self._repository = (
            repository
            if repository is not None
            else LecturerSectionsRepository()
        )

    def list_assigned_sections(self, user_id):
        if (
            not isinstance(user_id, str)
            or not user_id.strip()
            or len(user_id.strip()) > 12
        ):
            raise ValueError("Invalid lecturer session.")

        return self._repository.list_assigned_sections(
            user_id.strip()
        )
