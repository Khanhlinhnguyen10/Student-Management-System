
"""GradeScale model - Student Management System Group 05.

Matches the GradeScale class in the approved UML Class Diagram.

Grade boundaries must be configured from an approved grading
policy. No default letter-grade cutoffs are assumed.
"""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


def _decimal(value: object, field_name: str) -> Decimal:
    """Validate and convert a numeric value to Decimal."""

    if isinstance(value, bool) or not isinstance(
        value, (Decimal, int, float, str)
    ):
        raise ValueError(
            f"{field_name} must be numeric."
        )

    try:
        result = Decimal(str(value))

    except (InvalidOperation, ValueError):
        raise ValueError(
            f"{field_name} must be numeric."
        ) from None

    if not result.is_finite():
        raise ValueError(
            f"{field_name} must be finite."
        )

    return result


@dataclass(kw_only=True)
class GradeScale:
    letterGrade: str
    minScore: Decimal
    maxScore: Decimal
    gradePoint: Decimal

    def __post_init__(self) -> None:
        if (
            not isinstance(self.letterGrade, str)
            or not self.letterGrade.strip()
        ):
            raise ValueError(
                "letterGrade must be a nonempty string."
            )

        self.minScore = _decimal(
            self.minScore,
            "minScore"
        )

        self.maxScore = _decimal(
            self.maxScore,
            "maxScore"
        )

        self.gradePoint = _decimal(
            self.gradePoint,
            "gradePoint"
        )

        if not (
            Decimal("0")
            <= self.minScore
            <= self.maxScore
            <= Decimal("10")
        ):
            raise ValueError(
                "GradeScale bounds must satisfy "
                "0 <= minScore <= maxScore <= 10."
            )

    def convert(self, score: Decimal) -> str:
        """Convert a score within this interval to a letter grade."""

        value = _decimal(score, "score")

        if not (
            self.minScore
            <= value
            <= self.maxScore
        ):
            raise ValueError(
                "Score is outside this GradeScale interval."
            )

        return self.letterGrade
