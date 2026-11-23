
import unittest

from dataclasses import fields
from datetime import date
from decimal import Decimal

from app.models.faculty import Faculty
from app.models.major import Major
from app.models.course import Course
from app.models.semester import Semester


class AcademicModelsTestCase(unittest.TestCase):

    # ========================================
    # FACULTY MODEL TESTS
    # ========================================

    def test_faculty_attributes_match_data_model(self):
        expected = [
            "facultyId",
            "facultyCode",
            "facultyName",
            "email",
            "phoneNumber",
        ]

        actual = [
            item.name for item in fields(Faculty)
        ]

        self.assertEqual(actual, expected)

    def test_faculty_optional_contact_fields(self):
        faculty = Faculty(
            facultyId="F001",
            facultyCode="CNTT",
            facultyName="Information Technology",
        )

        self.assertIsNone(faculty.email)
        self.assertIsNone(faculty.phoneNumber)

    def test_faculty_operations_not_implemented(self):
        faculty = Faculty(
            facultyId="F001",
            facultyCode="CNTT",
            facultyName="Information Technology",
        )

        operations = [
            faculty.createFaculty,
            faculty.updateFaculty,
            faculty.deleteFaculty,
        ]

        for operation in operations:
            with self.subTest(
                operation=operation.__name__
            ):
                with self.assertRaises(
                    NotImplementedError
                ):
                    operation()

    # ========================================
    # MAJOR MODEL TEST
    # ========================================

    def test_major_attributes_match_data_model(self):
        expected = [
            "majorId",
            "facultyId",
            "majorName",
            "majorCode",
        ]

        actual = [
            item.name for item in fields(Major)
        ]

        self.assertEqual(actual, expected)

        major = Major(
            majorId="M001",
            facultyId="F001",
            majorName="Software Engineering",
            majorCode="KTPM",
        )

        self.assertEqual(major.facultyId, "F001")

    # ========================================
    # COURSE MODEL TESTS
    # ========================================

    def test_course_attributes_match_data_model(self):
        expected = [
            "courseId",
            "facultyId",
            "courseCode",
            "courseName",
            "credits",
            "midtermWeight",
            "assignmentWeight",
            "attendanceWeight",
            "finalExamWeight",
        ]

        actual = [
            item.name for item in fields(Course)
        ]

        self.assertEqual(actual, expected)

    def test_course_weights_use_decimal(self):
        course = Course(
            courseId="C001",
            facultyId="F001",
            courseCode="CS101",
            courseName="Programming Fundamentals",
            credits=3,
            midtermWeight=Decimal("0.20"),
            assignmentWeight=Decimal("0.20"),
            attendanceWeight=Decimal("0.10"),
            finalExamWeight=Decimal("0.50"),
        )

        weights = [
            course.midtermWeight,
            course.assignmentWeight,
            course.attendanceWeight,
            course.finalExamWeight,
        ]

        for weight in weights:
            self.assertIsInstance(weight, Decimal)

        self.assertEqual(
            sum(weights),
            Decimal("1.00")
        )

    # ========================================
    # SEMESTER MODEL TEST
    # ========================================

    def test_semester_attributes_match_data_model(self):
        expected = [
            "semesterId",
            "semesterName",
            "endDate",
            "startDate",
            "academicYear",
        ]

        actual = [
            item.name for item in fields(Semester)
        ]

        self.assertEqual(actual, expected)

        semester = Semester(
            semesterId="SEM001",
            semesterName="Semester 1",
            startDate=date(2026, 9, 1),
            endDate=date(2027, 1, 15),
            academicYear="2026-2027",
        )

        self.assertEqual(
            semester.academicYear,
            "2026-2027"
        )

        self.assertIsInstance(
            semester.startDate,
            date
        )

        self.assertIsInstance(
            semester.endDate,
            date
        )


if __name__ == "__main__":
    unittest.main()
