
from dataclasses import dataclass
from datetime import time


@dataclass(kw_only=True)
class ClassSection:
    """Class section mapped to the official ClassSections table."""

    classSectionId: str
    lecturerId: str | None = None
    courseId: str
    semesterId: str
    classCode: str
    maxCapacity: int
    currentEnrollment: int = 0
    room: str | None = None
    dayOfWeek: int | None = None
    startTime: time | None = None
    endTime: time | None = None

    def assignLecturer(self, lecturerId: str) -> bool:
        """UML operation; assignment rules belong in the Academic Service."""
        raise NotImplementedError(
            "Assign Lecturer is not implemented yet."
        )
