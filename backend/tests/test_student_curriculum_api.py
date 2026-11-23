
"""Tests for Student View Curriculum and authorization."""

from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from app import create_app

from app.controllers.auth_security import (
    SESSION_COOKIE_NAME,
)

from app.services.student_curriculum_service import (
    StudentCurriculumAmbiguousError,
    StudentCurriculumNotFoundError,
    StudentCurriculumService,
)


USER_ID = "USR000000002"
TOKEN = "c" * 43


def example_source():
    return {
        "studentId": "STU0000001",
        "majorId": "MJR0000001",
        "majorName": "Management Information Systems",
        "curricula": [
            {
                "curriculumId": "CUR0000001",
                "curriculumName": "MIS Curriculum",
                "academicYear": "2025-2026",
            }
        ],
        "courseRows": [
            {
                "curriculumId": "CUR0000001",
                "courseId": "CRS0000001",
                "courseCode": "DB101",
                "courseName": "Database Systems",
                "credits": 3,
                "courseType": "Required",
                "prerequisiteId": None,
                "prerequisiteCode": None,
                "prerequisiteName": None,
            },
            {
                "curriculumId": "CUR0000001",
                "courseId": "CRS0000002",
                "courseCode": "PR102",
                "courseName": "Programming",
                "credits": 3,
                "courseType": "Required",
                "prerequisiteId": "CRS0000001",
                "prerequisiteCode": "DB101",
                "prerequisiteName": "Database Systems",
            },
        ],
        "passedCourseIds": {"CRS0000001"},
    }


class StudentCurriculumServiceTests(unittest.TestCase):
    def setUp(self):
        self.repo = Mock()
        self.repo.load_curriculum.return_value = (
            example_source()
        )
        self.service = StudentCurriculumService(
            self.repo
        )

    def test_view_uses_authenticated_user(self):
        self.service.view_curriculum(USER_ID)

        self.repo.load_curriculum.assert_called_once_with(
            USER_ID
        )

    def test_returns_courses_and_prerequisites(self):
        result = self.service.view_curriculum(USER_ID)

        self.assertEqual(len(result["courses"]), 2)
        self.assertEqual(
            result["courses"][1]["prerequisites"][0]["courseCode"],
            "DB101",
        )

    def test_completion_uses_passing_results(self):
        result = self.service.view_curriculum(USER_ID)

        self.assertEqual(
            result["courses"][0]["status"],
            "Completed",
        )
        self.assertEqual(
            result["courses"][1]["status"],
            "Not Completed",
        )

    def test_duplicate_prerequisite_is_not_repeated(self):
        data = example_source()
        data["courseRows"].append(
            dict(data["courseRows"][1])
        )
        self.repo.load_curriculum.return_value = data

        result = self.service.view_curriculum(USER_ID)

        self.assertEqual(
            len(result["courses"][1]["prerequisites"]),
            1,
        )

    def test_missing_student_rejected(self):
        self.repo.load_curriculum.return_value = None

        with self.assertRaises(
            StudentCurriculumNotFoundError
        ):
            self.service.view_curriculum(USER_ID)

    def test_missing_curriculum_rejected(self):
        data = example_source()
        data["curricula"] = []
        self.repo.load_curriculum.return_value = data

        with self.assertRaises(
            StudentCurriculumNotFoundError
        ):
            self.service.view_curriculum(USER_ID)

    def test_ambiguous_curricula_rejected(self):
        data = example_source()
        data["curricula"].append({
            "curriculumId": "CUR0000002",
            "curriculumName": "Another Curriculum",
            "academicYear": "2026-2027",
        })
        self.repo.load_curriculum.return_value = data

        with self.assertRaises(
            StudentCurriculumAmbiguousError
        ):
            self.service.view_curriculum(USER_ID)

    def test_invalid_user_id_rejected(self):
        with self.assertRaises(ValueError):
            self.service.view_curriculum("")


class StudentCurriculumApiTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "curriculum-test-secret",
            "AUTH_ALLOWED_ORIGIN": "http://localhost:5173",
        })

        self.auth = Mock()
        self.auth.current_user.return_value = SimpleNamespace(
            user_id=USER_ID,
            role="Student",
        )
        self.app.extensions[
            "sms_auth_service"
        ] = self.auth

        self.service = Mock()
        self.service.view_curriculum.return_value = {
            "curriculumId": "CUR0000001",
            "courses": [],
        }
        self.app.extensions[
            "sms_student_curriculum_service"
        ] = self.service

        self.client = self.app.test_client()

    def _authenticate(self):
        self.client.set_cookie(
            SESSION_COOKIE_NAME,
            TOKEN,
            path="/api",
        )

    def test_guest_denied(self):
        response = self.client.get(
            "/api/student/curriculum"
        )

        self.assertEqual(response.status_code, 401)

    def test_administrator_denied(self):
        self._authenticate()
        self.auth.current_user.return_value.role = (
            "Administrator"
        )

        response = self.client.get(
            "/api/student/curriculum"
        )

        self.assertEqual(response.status_code, 403)
        self.service.view_curriculum.assert_not_called()

    def test_student_can_view_own_curriculum(self):
        self._authenticate()

        response = self.client.get(
            "/api/student/curriculum"
        )

        self.assertEqual(response.status_code, 200)
        self.service.view_curriculum.assert_called_once_with(
            USER_ID
        )

    def test_profile_uses_no_store_cache(self):
        self._authenticate()

        response = self.client.get(
            "/api/student/curriculum"
        )

        self.assertEqual(
            response.headers["Cache-Control"],
            "no-store",
        )

    def test_not_found_returns_404(self):
        self._authenticate()
        self.service.view_curriculum.side_effect = (
            StudentCurriculumNotFoundError(
                "No curriculum found."
            )
        )

        response = self.client.get(
            "/api/student/curriculum"
        )

        self.assertEqual(response.status_code, 404)

    def test_ambiguous_returns_409(self):
        self._authenticate()
        self.service.view_curriculum.side_effect = (
            StudentCurriculumAmbiguousError(
                "Multiple curricula exist."
            )
        )

        response = self.client.get(
            "/api/student/curriculum"
        )

        self.assertEqual(response.status_code, 409)

    def test_database_error_is_not_disclosed(self):
        self._authenticate()
        self.service.view_curriculum.side_effect = (
            RuntimeError("PRIVATE_DATABASE_ERROR")
        )

        response = self.client.get(
            "/api/student/curriculum"
        )

        self.assertEqual(response.status_code, 503)
        self.assertNotIn(
            "PRIVATE_DATABASE_ERROR",
            str(response.json),
        )


if __name__ == "__main__":
    unittest.main()
