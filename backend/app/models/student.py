
from dataclasses import dataclass

from app.models.user import User


@dataclass(kw_only=True)
class Student(User):
    """Student: inherits User; majorId maps to the Majors FK."""

    studentId: str
    majorId: str
    academicStatus: str

    def logIn(self, username: str, password: str) -> bool:
        raise NotImplementedError("Login is not implemented yet.")

    def updateContact(self) -> bool:
        raise NotImplementedError("Update Contact is not implemented yet.")

    def viewCurriculum(self):
        raise NotImplementedError("View Curriculum is not implemented yet.")

    def viewAcademicTranscript(self):
        raise NotImplementedError(
            "View Academic Transcript is not implemented yet."
        )
