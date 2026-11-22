
from dataclasses import dataclass

from app.models.user import User


@dataclass(kw_only=True)
class Lecturer(User):
    """Lecturer: inherits User; facultyId maps to the Faculties FK."""

    lecturerId: str
    facultyId: str

    def logIn(self, username: str, password: str) -> bool:
        raise NotImplementedError("Login is not implemented yet.")

    def updateContact(self) -> bool:
        raise NotImplementedError("Update Contact is not implemented yet.")

    def manageGrades(self) -> bool:
        raise NotImplementedError("Manage Grades is not implemented yet.")
