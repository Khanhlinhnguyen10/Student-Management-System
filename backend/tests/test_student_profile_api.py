
"""Student Profile API and business-service tests."""

from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from app import create_app

from app.controllers.auth_security import (
    SESSION_COOKIE_NAME,
    csrf_token_for_session,
)

from app.services.student_profile_service import (
    StudentContactValidationError,
    StudentProfileNotFoundError,
    StudentProfileService,
)


TOKEN = "t" * 43
USER_ID = "USR000000002"

PROFILE = {
    "username": "student01",
    "studentId": "STU0000001",
    "citizenId": "079000000002",
    "fullName": "Tran Minh Anh",
    "dateOfBirth": "2005-03-12",
    "email": "student01@example.test",
    "phoneNumber": "0900000002",
    "gender": "Female",
    "facultyName": "Information Technology",
    "majorName": "Management Information Systems",
    "academicStatus": "Active",
    "majorId": "MJR0000001",
}


class StudentProfileApiTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "student-profile-test-secret",
            "AUTH_ALLOWED_ORIGIN": "http://localhost:5173",
        })

        self.auth = Mock()
        self.auth.current_user.return_value = SimpleNamespace(
            user_id=USER_ID,
            role="Student",
        )
        self.app.extensions["sms_auth_service"] = self.auth

        self.service = Mock()
        self.service.view_profile.return_value = dict(PROFILE)
        self.service.update_information.return_value = dict(PROFILE)

        self.app.extensions[
            "sms_student_profile_service"
        ] = self.service

        self.client = self.app.test_client()

    def _login(self):
        self.client.set_cookie(
            SESSION_COOKIE_NAME,
            TOKEN,
            path="/api",
        )

    def _headers(self):
        with self.app.app_context():
            csrf = csrf_token_for_session(TOKEN)

        return {
            "Origin": "http://localhost:5173",
            "X-CSRF-Token": csrf,
        }

    def test_unauthenticated_get_returns_401(self):
        response = self.client.get("/api/student/profile")
        self.assertEqual(response.status_code, 401)

    def test_lecturer_cannot_view_student_profile(self):
        self._login()
        self.auth.current_user.return_value.role = "Lecturer"

        response = self.client.get("/api/student/profile")

        self.assertEqual(response.status_code, 403)
        self.service.view_profile.assert_not_called()

    def test_student_views_own_profile(self):
        self._login()

        response = self.client.get("/api/student/profile")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json["profile"]["studentId"],
            "STU0000001",
        )
        self.service.view_profile.assert_called_once_with(
            USER_ID
        )

    def test_profile_response_is_not_cached(self):
        self._login()

        response = self.client.get("/api/student/profile")

        self.assertEqual(
            response.headers["Cache-Control"],
            "no-store",
        )

    def test_profile_not_found_returns_404(self):
        self._login()
        self.service.view_profile.side_effect = (
            StudentProfileNotFoundError()
        )

        response = self.client.get("/api/student/profile")

        self.assertEqual(response.status_code, 404)

    def test_student_updates_contact(self):
        self._login()

        payload = {
            "email": "student01@example.test",
            "phoneNumber": "0900000002",
        }

        response = self.client.put(
            "/api/student/profile",
            json=payload,
            headers=self._headers(),
        )

        self.assertEqual(response.status_code, 200)
        self.service.update_information.assert_called_once_with(
            USER_ID,
            payload,
        )

    def test_update_rejects_missing_csrf(self):
        self._login()

        response = self.client.put(
            "/api/student/profile",
            json={"email": None, "phoneNumber": None},
            headers={"Origin": "http://localhost:5173"},
        )

        self.assertEqual(response.status_code, 403)
        self.service.update_information.assert_not_called()

    def test_update_rejects_foreign_origin(self):
        self._login()

        headers = self._headers()
        headers["Origin"] = "http://malicious.example"

        response = self.client.put(
            "/api/student/profile",
            json={"email": None, "phoneNumber": None},
            headers=headers,
        )

        self.assertEqual(response.status_code, 403)
        self.service.update_information.assert_not_called()

    def test_update_rejects_lecturer_role(self):
        self._login()
        self.auth.current_user.return_value.role = "Lecturer"

        response = self.client.put(
            "/api/student/profile",
            json={"email": None, "phoneNumber": None},
            headers=self._headers(),
        )

        self.assertEqual(response.status_code, 403)
        self.service.update_information.assert_not_called()

    def test_update_validation_error_returns_400(self):
        self._login()
        self.service.update_information.side_effect = (
            StudentContactValidationError(
                "Non-editable fields: citizenId"
            )
        )

        response = self.client.put(
            "/api/student/profile",
            json={"citizenId": "INVALID"},
            headers=self._headers(),
        )

        self.assertEqual(response.status_code, 400)

    def test_unexpected_database_error_returns_503(self):
        self._login()
        self.service.view_profile.side_effect = (
            RuntimeError("PRIVATE_DATABASE_ERROR")
        )

        response = self.client.get("/api/student/profile")

        self.assertEqual(response.status_code, 503)
        self.assertNotIn(
            "PRIVATE_DATABASE_ERROR",
            str(response.json),
        )


class StudentProfileServiceTests(unittest.TestCase):
    def setUp(self):
        self.repo = Mock()
        self.repo.get_profile.return_value = dict(PROFILE)
        self.repo.update_contact.return_value = dict(PROFILE)
        self.service = StudentProfileService(self.repo)

    def test_view_uses_authenticated_user_id(self):
        profile = self.service.view_profile(USER_ID)

        self.assertEqual(profile["studentId"], "STU0000001")
        self.repo.get_profile.assert_called_once_with(USER_ID)

    def test_update_accepts_valid_contact(self):
        payload = {
            "email": "student01@example.test",
            "phoneNumber": "0900000002",
        }

        self.service.update_information(USER_ID, payload)

        self.repo.update_contact.assert_called_once_with(
            USER_ID,
            email="student01@example.test",
            phone_number="0900000002",
        )

    def test_update_rejects_protected_fields(self):
        payload = {
            "email": "student01@example.test",
            "phoneNumber": "0900000002",
            "citizenId": "079000000099",
        }

        with self.assertRaises(
            StudentContactValidationError
        ):
            self.service.update_information(USER_ID, payload)

        self.repo.update_contact.assert_not_called()

    def test_update_rejects_invalid_email(self):
        with self.assertRaises(
            StudentContactValidationError
        ):
            self.service.update_information(
                USER_ID,
                {
                    "email": "not-an-email",
                    "phoneNumber": "0900000002",
                },
            )

    def test_update_rejects_invalid_phone(self):
        with self.assertRaises(
            StudentContactValidationError
        ):
            self.service.update_information(
                USER_ID,
                {
                    "email": "student01@example.test",
                    "phoneNumber": "INVALID",
                },
            )

    def test_update_missing_profile_raises_404_domain_error(self):
        self.repo.update_contact.return_value = None

        with self.assertRaises(
            StudentProfileNotFoundError
        ):
            self.service.update_information(
                USER_ID,
                {
                    "email": None,
                    "phoneNumber": None,
                },
            )


if __name__ == "__main__":
    unittest.main()
