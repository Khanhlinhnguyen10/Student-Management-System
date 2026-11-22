
from decimal import Decimal, InvalidOperation


class GradeValidator:
    """Validate grade inputs using the final Group 05 Data Model.

    Grade component columns and weight columns are DECIMAL(4,2).
    Grade marks must lie in the inclusive interval [0, 10].
    """

    MARK_FIELDS = (
        "midtermMark",
        "assignmentMark",
        "attendanceMark",
        "finalExamMark",
    )

    WEIGHT_FIELDS = (
        "midtermWeight",
        "assignmentWeight",
        "attendanceWeight",
        "finalExamWeight",
    )

    @staticmethod
    def _to_decimal(value, field_name: str) -> Decimal:
        if isinstance(value, bool) or not isinstance(
            value, (Decimal, int, float, str)
        ):
            raise ValueError(f"{field_name} must be a valid number.")

        try:
            number = Decimal(str(value))
        except (InvalidOperation, ValueError):
            raise ValueError(
                f"{field_name} must be a valid number."
            ) from None

        if not number.is_finite():
            raise ValueError(f"{field_name} must be a finite number.")

        # Do not silently round values that SQL DECIMAL(4,2) cannot store.
        try:
            too_precise = number != number.quantize(Decimal("0.01"))
        except InvalidOperation:
            raise ValueError(
                f"{field_name} cannot be represented with 2 decimal places."
            ) from None

        if too_precise:
            raise ValueError(
                f"{field_name} must have at most 2 decimal places."
            )

        return number

    @classmethod
    def validate_mark(
        cls, value, field_name: str, *, required: bool = False
    ) -> Decimal | None:
        """Validate one grade; None is allowed for a draft gradebook."""
        if field_name not in cls.MARK_FIELDS:
            raise ValueError(f"Unknown grade component: {field_name}.")

        if value is None:
            if required:
                raise ValueError(f"{field_name} is required to calculate a grade.")
            return None

        mark = cls._to_decimal(value, field_name)
        if not Decimal("0") <= mark <= Decimal("10"):
            raise ValueError(f"{field_name} must be between 0 and 10.")
        return mark

    @classmethod
    def validate_gradebook(
        cls, gradebook, *, require_complete: bool = False
    ) -> dict[str, Decimal | None]:
        """Validate all four marks without modifying the GradeBook object."""
        return {
            field: cls.validate_mark(
                getattr(gradebook, field), field, required=require_complete
            )
            for field in cls.MARK_FIELDS
        }

    @classmethod
    def validate_weights(cls, course, *, weight_total) -> dict[str, Decimal]:
        """Check four nonnegative weights and their explicitly supplied total.

        The final requirement does not specify whether course weights are
        stored as fractions totaling 1 or percentages totaling 100.
        The caller must supply the approved weight_total convention.
        """
        total = cls._to_decimal(weight_total, "weight_total")
        if total <= 0:
            raise ValueError("weight_total must be greater than zero.")

        weights = {}
        for field in cls.WEIGHT_FIELDS:
            weight = cls._to_decimal(getattr(course, field), field)
            if weight < 0:
                raise ValueError(f"{field} cannot be negative.")
            weights[field] = weight

        if sum(weights.values(), Decimal("0")) != total:
            raise ValueError(
                "The four course weights must sum to weight_total."
            )
        return weights
