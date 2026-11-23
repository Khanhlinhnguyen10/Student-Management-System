
import unittest
from decimal import Decimal

from app.models.course import Course
from app.models.gradebook import GradeBook
from app.services.grade_service import GradeService
from app.validators.grade_validator import GradeValidator


class GradeBusinessTestCase(unittest.TestCase):
    def setUp(self):
        self.gradebook = GradeBook(
            gradebookId="GB001",
            enrollmentId="E001",
            midtermMark=Decimal("7.00"),
            assignmentMark=Decimal("8.00"),
            attendanceMark=Decimal("9.00"),
            finalExamMark=Decimal("8.00"),
        )
        self.course = Course(
            courseId="C001",
            facultyId="F001",
            courseCode="CS101",
            courseName="Example Course",
            credits=3,
            midtermWeight=Decimal("0.20"),
            assignmentWeight=Decimal("0.20"),
            attendanceWeight=Decimal("0.10"),
            finalExamWeight=Decimal("0.50"),
        )

    def test_marks_accept_boundaries_zero_and_ten(self):
        self.assertEqual(
            GradeValidator.validate_mark("0", "midtermMark"), Decimal("0")
        )
        self.assertEqual(
            GradeValidator.validate_mark("10", "finalExamMark"), Decimal("10")
        )

    def test_marks_reject_values_outside_range(self):
        for value in ("-0.01", "10.01"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    GradeValidator.validate_mark(value, "assignmentMark")

    def test_marks_reject_bad_numbers(self):
        for value in (True, "not-a-number", "NaN", "Infinity", "8.123", "1e999999"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    GradeValidator.validate_mark(value, "attendanceMark")

    def test_draft_grade_can_have_missing_marks(self):
        draft = GradeBook(gradebookId="GB002", enrollmentId="E002")
        values = GradeValidator.validate_gradebook(draft)
        self.assertTrue(all(value is None for value in values.values()))

    def test_calculation_requires_all_four_marks(self):
        self.gradebook.finalExamMark = None
        with self.assertRaisesRegex(ValueError, "finalExamMark"):
            GradeService.calculate_final_score(
                self.gradebook, self.course, weight_total=Decimal("1.00")
            )

    def test_score_calculated_with_fractional_weights(self):
        result = GradeService.calculate_final_score(
            self.gradebook, self.course, weight_total=Decimal("1.00")
        )
        self.assertEqual(result, Decimal("7.90"))

    def test_score_calculated_with_percentage_weights(self):
        self.course.midtermWeight = Decimal("20.00")
        self.course.assignmentWeight = Decimal("20.00")
        self.course.attendanceWeight = Decimal("10.00")
        self.course.finalExamWeight = Decimal("50.00")
        result = GradeService.calculate_final_score(
            self.gradebook, self.course, weight_total=Decimal("100.00")
        )
        self.assertEqual(result, Decimal("7.90"))

    def test_wrong_weight_total_is_rejected(self):
        self.course.finalExamWeight = Decimal("0.40")
        with self.assertRaisesRegex(ValueError, "sum to weight_total"):
            GradeService.calculate_final_score(
                self.gradebook, self.course, weight_total=Decimal("1.00")
            )

    def test_negative_weight_is_rejected(self):
        self.course.assignmentWeight = Decimal("-0.20")
        with self.assertRaisesRegex(ValueError, "assignmentWeight"):
            GradeService.calculate_final_score(
                self.gradebook, self.course, weight_total=Decimal("1.00")
            )

    def test_calculation_does_not_finalize_or_mutate_gradebook(self):
        result = GradeService.calculate_final_score(
            self.gradebook, self.course, weight_total=Decimal("1.00")
        )
        self.assertEqual(result, Decimal("7.90"))
        self.assertIsNone(self.gradebook.finalScore)
        self.assertIsNone(self.gradebook.letterGrade)
        self.assertFalse(self.gradebook.isFinalized)

    def test_no_unapproved_letter_grade_or_gpa_calculation(self):
        self.assertFalse(hasattr(GradeService, "to_letter_grade"))
        self.assertFalse(hasattr(GradeService, "calculate_gpa"))


if __name__ == "__main__":
    unittest.main()
