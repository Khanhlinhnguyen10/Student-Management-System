
import unittest
from dataclasses import fields
from decimal import Decimal

from app.models.gradebook import GradeBook
from app.models.semester_results import SemesterResults


class GradeModelsTestCase(unittest.TestCase):

    def test_gradebook_fields_match_final_data_model(self):
        self.assertEqual(
            [item.name for item in fields(GradeBook)],
            [
                "gradebookId",
                "enrollmentId",
                "midtermMark",
                "assignmentMark",
                "attendanceMark",
                "finalExamMark",
                "finalScore",
                "letterGrade",
                "isFinalized",
            ],
        )

    def test_new_gradebook_is_draft_with_empty_marks(self):
        grade = GradeBook(
            gradebookId="GB001",
            enrollmentId="E001",
        )

        self.assertFalse(grade.isFinalized)

        for name in (
            "midtermMark",
            "assignmentMark",
            "attendanceMark",
            "finalExamMark",
            "finalScore",
            "letterGrade",
        ):
            with self.subTest(field=name):
                self.assertIsNone(getattr(grade, name))

    def test_gradebook_marks_accept_decimal(self):
        grade = GradeBook(
            gradebookId="GB001",
            enrollmentId="E001",
            midtermMark=Decimal("7.50"),
            assignmentMark=Decimal("8.00"),
            attendanceMark=Decimal("9.00"),
            finalExamMark=Decimal("8.25"),
        )

        for mark in (
            grade.midtermMark,
            grade.assignmentMark,
            grade.attendanceMark,
            grade.finalExamMark,
        ):
            self.assertIsInstance(mark, Decimal)

    def test_gradebook_can_represent_finalized_state(self):
        grade = GradeBook(
            gradebookId="GB001",
            enrollmentId="E001",
            finalScore=Decimal("8.00"),
            letterGrade="B",
            isFinalized=True,
        )

        self.assertTrue(grade.isFinalized)

    def test_gradebook_uml_operations_are_pending(self):
        grade = GradeBook(
            gradebookId="GB001",
            enrollmentId="E001",
        )

        with self.assertRaises(NotImplementedError):
            grade.calculateFinalScore()

        with self.assertRaises(NotImplementedError):
            grade.toLetterGrade(Decimal("8.00"))

    def test_semester_results_fields_match_final_data_model(self):
        self.assertEqual(
            [item.name for item in fields(SemesterResults)],
            [
                "studentId",
                "semesterId",
                "semesterGPA",
                "cumulativeGPA",
            ],
        )

    def test_semester_results_composite_key_parts(self):
        result = SemesterResults(
            studentId="ST001",
            semesterId="SEM001",
        )

        self.assertEqual(
            (result.studentId, result.semesterId),
            ("ST001", "SEM001"),
        )

        self.assertIsNone(result.semesterGPA)
        self.assertIsNone(result.cumulativeGPA)

    def test_semester_results_use_decimal_scores(self):
        result = SemesterResults(
            studentId="ST001",
            semesterId="SEM001",
            semesterGPA=Decimal("3.25"),
            cumulativeGPA=Decimal("3.10"),
        )

        self.assertIsInstance(
            result.semesterGPA,
            Decimal,
        )

        self.assertIsInstance(
            result.cumulativeGPA,
            Decimal,
        )

    def test_semester_results_uml_operations_are_pending(self):
        result = SemesterResults(
            studentId="ST001",
            semesterId="SEM001",
        )

        with self.assertRaises(NotImplementedError):
            result.calculateGPA("SEM001")

        with self.assertRaises(NotImplementedError):
            result.calculateCGPA()


if __name__ == "__main__":
    unittest.main()
