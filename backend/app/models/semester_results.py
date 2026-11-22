
from dataclasses import dataclass
from decimal import Decimal


@dataclass(kw_only=True)
class SemesterResults:
    """SemesterResults record following the final Group 05 Data Model.

    (studentId, semesterId) is a composite primary key in SQL Server.
    The UML transcriptId is not a column in the final Data Model.
    """

    studentId: str
    semesterId: str
    semesterGPA: Decimal | None = None
    cumulativeGPA: Decimal | None = None

    def calculateGPA(self, semesterId: str) -> Decimal:
        """UML operation; depends on finalized results and credit weights."""
        raise NotImplementedError(
            "Semester GPA requires finalized grades and GPA conversion rules."
        )

    def calculateCGPA(self) -> Decimal:
        """UML operation; depends on the student's finalized academic history."""
        raise NotImplementedError(
            "Cumulative GPA requires finalized grades and GPA conversion rules."
        )
