
"""Unit tests for Student Academic Transcript - Group 05."""

from decimal import Decimal
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from app import create_app

from app.controllers.auth_security import SESSION_COOKIE_NAME

from app.repositories.student_transcript_repository import (
    _GRADES_SQL,
)

from app.services.student_transcript_service import (
    StudentTranscriptNotFoundError,
    StudentTranscriptService,
)


USER_ID = "USR000000002"
TOKEN = "t" * 43


def sample_source():
    """Mock data, not an actual SQL Server result."""
    return {
        "studentId": "STU0000001",
        "grades": [
            {
                "semesterId": "SEM0000001",
                "semesterName": "Semester 1",
                "academicYear": "2025-2026",
                "classCode": "DBI101.01",
                "courseId": "CRS0000001",
                "courseCode": "DBI101",
                "courseName": "Database Systems",
                "credits": 3,
                "midtermMark": Decimal("8.00"),
                "assignmentMark": Decimal("8.50"),
                "attendanceMark": Decimal("9.00"),
                "finalExamMark": Decimal("8.50"),
                "finalScore": Decimal("8.45"),
                "letterGrade": "B+",
                "gradePoint": Decimal("3.50"),
            },
            {
                "semesterId": "SEM0000002",
                "semesterName": "Semester 2",
                "academicYear": "2025-2026",
                "classCode": "PRG102.01",
                "courseId": "CRS0000002",
                "courseCode": "PRG102",
                "courseName": "Python Programming",
                "credits": 3,
                "midtermMark": Decimal("9.00"),
                "assignmentMark": Decimal("9.00"),
                "attendanceMark": Decimal("9.00"),
                "finalExamMark": Decimal("9.00"),
                "finalScore": Decimal("9.00"),
                "letterGrade": "A",
                "gradePoint": Decimal("4.00"),
            },
        ],
        "semesterResults": [
            {
                "semesterId": "SEM0000001",
                "semesterName": "Semester 1",
                "academicYear": "2025-2026",
                "semesterGPA": Decimal("3.50"),
                "cumulativeGPA": Decimal("3.50"),
            },
            {
                "semesterId": "SEM0000002",
                "semesterName": "Semester 2",
                "academicYear": "2025-2026",
                "semesterGPA": Decimal("4.00"),
                "cumulativeGPA": Decimal("3.75"),
            },
        ],
    }


class StudentTranscriptServiceTests(unittest.TestCase):
    def setUp(self):
        self.repo = Mock()
        self.repo.get_transcript.return_value = sample_source()
        self.service = StudentTranscriptService(self.repo)

    def test_uses_authenticated_user_id(self):
        self.service.view_transcript(USER_ID)

        self.repo.get_transcript.assert_called_once_with(
            USER_ID
        )

    def test_invalid_user_id_rejected(self):
        with self.assertRaises(ValueError):
            self.service.view_transcript("")

        self.repo.get_transcript.assert_not_called()

    def test_missing_student_rejected(self):
        self.repo.get_transcript.return_value = None

        with self.assertRaises(StudentTranscriptNotFoundError):
            self.service.view_transcript(USER_ID)

    def test_groups_courses_by_semester(self):
        result = self.service.view_transcript(USER_ID)

        self.assertEqual(len(result["semesters"]), 2)
        self.assertEqual(
            result["semesters"][0]["courses"][0]["courseCode"],
            "DBI101",
        )
        self.assertEqual(
            result["semesters"][1]["courses"][0]["courseCode"],
            "PRG102",
        )

    def test_decimal_values_are_serialized(self):
        result = self.service.view_transcript(USER_ID)

        first_course = result["semesters"][0]["courses"][0]

        self.assertEqual(first_course["finalScore"], 8.45)
        self.assertIsInstance(first_course["finalScore"], float)
        self.assertEqual(
            result["semesters"][0]["semesterGPA"],
            3.50,
        )

    def test_latest_cumulative_gpa(self):
        result = self.service.view_transcript(USER_ID)

        self.assertEqual(
            result["latestCumulativeGPA"],
            3.75,
        )
        self.assertEqual(result["totalFinalizedResults"], 2)
        self.assertTrue(result["hasFinalizedGrades"])

    def test_empty_grades_return_empty_transcript(self):
        self.repo.get_transcript.return_value = {
            "studentId": "STU0000001",
            "grades": [],
            "semesterResults": [],
        }

        result = self.service.view_transcript(USER_ID)

        self.assertFalse(result["hasFinalizedGrades"])
        self.assertEqual(result["semesters"], [])
        self.assertIsNone(result["latestCumulativeGPA"])


class StudentTranscriptApiTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "transcript-unit-test-secret",
            "AUTH_ALLOWED_ORIGIN": "http://localhost:5173",
        })

        self.auth = Mock()
        self.auth.current_user.return_value = SimpleNamespace(
            user_id=USER_ID,
            role="Student",
        )
        self.app.extensions["sms_auth_service"] = self.auth

        self.transcript_service = Mock()
        self.transcript_service.view_transcript.return_value = {
            "studentId": "STU0000001",
            "hasFinalizedGrades": True,
            "totalFinalizedResults": 2,
            "latestCumulativeGPA": 3.75,
            "semesters": [],
        }

        self.app.extensions[
            "sms_student_transcript_service"
        ] = self.transcript_service

        self.client = self.app.test_client()

    def login(self):
        self.client.set_cookie(
            SESSION_COOKIE_NAME,
            TOKEN,
            path="/api",
        )

    def test_guest_gets_401(self):
        response = self.client.get("/api/student/transcript")

        self.assertEqual(response.status_code, 401)
        self.transcript_service.view_transcript.assert_not_called()

    def test_admin_gets_403(self):
        self.login()
        self.auth.current_user.return_value.role = "Administrator"

        response = self.client.get("/api/student/transcript")

        self.assertEqual(response.status_code, 403)
        self.transcript_service.view_transcript.assert_not_called()

    def test_lecturer_gets_403(self):
        self.login()
        self.auth.current_user.return_value.role = "Lecturer"

        response = self.client.get("/api/student/transcript")

        self.assertEqual(response.status_code, 403)

    def test_student_gets_200(self):
        self.login()

        response = self.client.get("/api/student/transcript")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json["transcript"]["studentId"],
            "STU0000001",
        )
        self.transcript_service.view_transcript.assert_called_once_with(
            USER_ID
        )

    def test_query_cannot_select_another_student(self):
        self.login()

        response = self.client.get(
            "/api/student/transcript?studentId=STU0000002"
        )

        self.assertEqual(response.status_code, 200)

        # The server uses the session identity, not query parameters.
        self.transcript_service.view_transcript.assert_called_once_with(
            USER_ID
        )

    def test_transcript_is_not_cached(self):
        self.login()

        response = self.client.get("/api/student/transcript")

        self.assertEqual(
            response.headers["Cache-Control"],
            "no-store",
        )

    def test_not_found_gets_404(self):
        self.login()
        self.transcript_service.view_transcript.side_effect = (
            StudentTranscriptNotFoundError()
        )

        response = self.client.get("/api/student/transcript")

        self.assertEqual(response.status_code, 404)

    def test_database_error_gets_503_without_leak(self):
        self.login()
        self.transcript_service.view_transcript.side_effect = (
            RuntimeError("PRIVATE_SQL_SERVER_ERROR")
        )

        response = self.client.get("/api/student/transcript")

        self.assertEqual(response.status_code, 503)
        self.assertNotIn(
            "PRIVATE_SQL_SERVER_ERROR",
            str(response.json),
        )


class TranscriptRepositorySafetyTests(unittest.TestCase):
    def test_sql_filters_finalized_grades(self):
        normalized_sql = " ".join(_GRADES_SQL.split()).lower()

        self.assertIn(
            "gb.isfinalized = 1",
            normalized_sql,
        )

        self.assertIn(
            "e.studentid = ?",
            normalized_sql,
        )


if __name__ == "__main__":
    unittest.main()
