
from decimal import Decimal

from app.validators.grade_validator import GradeValidator


class GradeService:
    """Pure grade calculations for DFD 4.0 Grade Management.

    No HTTP handling and no SQL queries belong in this service method.
    Authorization, database transactions, finalization, grade-letter
    conversion, and GPA updates must be implemented separately.
    """

    @staticmethod
    def calculate_final_score(
        gradebook, course, *, weight_total: Decimal
    ) -> Decimal:
        """Return the exact weighted result, without guessing rounding rules.

        weight_total is explicitly supplied because the requirement does not
        specify whether weights are stored as fractions or percentages.
        """
        marks = GradeValidator.validate_gradebook(
            gradebook, require_complete=True
        )
        weights = GradeValidator.validate_weights(
            course, weight_total=weight_total
        )

        numerator = (
            marks["midtermMark"] * weights["midtermWeight"]
            + marks["assignmentMark"] * weights["assignmentWeight"]
            + marks["attendanceMark"] * weights["attendanceWeight"]
            + marks["finalExamMark"] * weights["finalExamWeight"]
        )
        return numerator / Decimal(str(weight_total))
