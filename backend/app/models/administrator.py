
from dataclasses import dataclass

from app.models.user import User


@dataclass(kw_only=True)
class Administrator(User):
    """Administrator: inherits User, maps adminId in SQL Server."""

    adminId: str

    def logIn(self, username: str, password: str) -> bool:
        raise NotImplementedError("Login is not implemented yet.")

    def createAccount(self) -> bool:
        raise NotImplementedError("Create Account is not implemented yet.")

    def manageUsers(self) -> bool:
        raise NotImplementedError("Manage Users is not implemented yet.")

    def manageFaculties(self) -> bool:
        raise NotImplementedError("Manage Faculties is not implemented yet.")

    def manageCourses(self) -> bool:
        raise NotImplementedError("Manage Courses is not implemented yet.")

    def manageSemesters(self) -> bool:
        raise NotImplementedError("Manage Semesters is not implemented yet.")

    def manageClassSections(self) -> bool:
        raise NotImplementedError("Manage Class Sections is not implemented yet.")
