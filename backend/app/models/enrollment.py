
from dataclasses import dataclass
from datetime import date


@dataclass(kw_only=True)
class Enrollment:
    """Enrollment record mapped to the official Enrollments table."""

    enrollmentId: str
    studentId: str
    classSectionId: str
    enrollmentDate: date

    def registerCourse(self) -> bool:
        """Declared in UML; no independent registration Use Case is specified."""
        raise NotImplementedError(
            "Register Course is not implemented yet."
        )

    def cancelEnrollment(self) -> bool:
        """Declared in UML; do not expose an API without an agreed Use Case."""
        raise NotImplementedError(
            "Cancel Enrollment is not implemented yet."
        )
