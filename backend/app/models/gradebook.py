
from dataclasses import dataclass
from decimal import Decimal


@dataclass(kw_only=True)
class GradeBook:
    """GradeBooks record following the final Group 05 Data Model.

    Grading rules belong to the Grade Management business flow.
    """

    gradebookId: str
    enrollmentId: str
    midtermMark: Decimal | None = None
    assignmentMark: Decimal | None = None
    attendanceMark: Decimal | None = None
    finalExamMark: Decimal | None = None
    finalScore: Decimal | None = None
    letterGrade: str | None = None
    isFinalized: bool = False

    def calculateFinalScore(self) -> Decimal:
        """UML operation; requires course weights from the related Course."""
        raise NotImplementedError(
            "Final-score calculation requires Course weights and GradeService."
        )

    def toLetterGrade(self, score: Decimal) -> str:
        """UML operation; no official letter-grade cutoffs are specified yet."""
        raise NotImplementedError(
            "Letter-grade conversion requires an approved grading scale."
        )
