
"""Tests for Group 05 Create Account Controller.

Use Case 11:
- Administrator-only access
- CSRF and Origin protection
- Faculty/Major options
- Input validation
- Error handling
- One-time credential handoff after database commit
- Required account fields

All tests use mocks and do not modify SQL Server.
"""

import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from app import create_app

from app.controllers.auth_security import (
    csrf_token_for_session,
)

from app.repositories.create_account_repository import (
    AccountAlreadyExistsError,
    AccountReferenceError,
)

from app.services.create_account_service import (
    CreateAccountService,
    CreateAccountValidationError,
)


STUDENT_DATA = {
    "accountType": "Student",
    "username": "student_test01",
    "citizenId": "079000001234",
    "fullName": "Test Student",
    "dateOfBirth": "2005-04-15",
    "email": "student@example.test",
    "phoneNumber": "0901234567",
    "gender": "Female",
    "majorId": "MAJ0000001",
    "academicStatus": "Active",
}


class CreateAccountRequiredFieldsTests(unittest.TestCase):
    """Business validation from Use Case 11."""

    def setUp(self):
        self.repo = Mock()
        self.service = CreateAccountService(
            repository=self.repo
        )

    def _assert_required(self, field):
        payload = dict(STUDENT_DATA)
        payload.pop(field)

        with self.assertRaises(
            CreateAccountValidationError
        ):
            self.service.create_record(payload)

        self.repo.create_account.assert_not_called()

    def test_date_of_birth_required(self):
        self._assert_required("dateOfBirth")

    def test_email_required(self):
        self._assert_required("email")

    def test_phone_number_required(self):
        self._assert_required("phoneNumber")

    def test_gender_required(self):
        self._assert_required("gender")


class AdminCreateAccountAPITests(unittest.TestCase):
    """HTTP tests with mocked authentication and services."""

    def setUp(self):
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "unit-test-secret",
            "AUTH_ALLOWED_ORIGIN": "http://localhost:5173",
        })

        self.auth_service = Mock()

        self.auth_service.current_user.return_value = (
            SimpleNamespace(role="Administrator")
        )

        self.app.extensions[
            "sms_auth_service"
        ] = self.auth_service

        self.create_service = Mock()

        self.app.extensions[
            "sms_create_account_service"
        ] = self.create_service

        self.client = self.app.test_client()

        self.client.set_cookie(
            "sms_auth",
            "unit-test-session",
            path="/api",
        )

        with self.app.app_context():
            csrf = csrf_token_for_session(
                "unit-test-session"
            )

        self.headers = {
            "Origin": "http://localhost:5173",
            "X-CSRF-Token": csrf,
        }

        self.url = "/api/admin/create-account"

    def _configure_creation_result(self):
        self.create_service.create_record.return_value = {
            "account": {
                "accountType": "Student",
                "userId": "USR000000007",
                "studentId": "STU0000004",
                "lecturerId": None,
                "username": "student_test01",
                "fullName": "Test Student",
            },
            "initialCredentials": {
                "username": "student_test01",
                "initialPassword": "internal-test-password",
            },
        }

    # =========================================
    # GET OPTIONS
    # =========================================

    def test_get_faculties(self):
        self.create_service.list_faculties.return_value = [
            {
                "facultyId": "FAC0000001",
                "facultyName": "Information Technology",
            }
        ]

        response = self.client.get(
            self.url + "/faculties"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            len(response.get_json()["faculties"]),
            1,
        )

    def test_get_majors(self):
        self.create_service.list_majors.return_value = [
            {
                "majorId": "MAJ0000001",
                "majorName": "Information Technology",
                "facultyId": "FAC0000001",
                "facultyName": "Information Technology",
            }
        ]

        response = self.client.get(
            self.url + "/majors"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            len(response.get_json()["majors"]),
            1,
        )

    # =========================================
    # AUTHORIZATION
    # =========================================

    def test_requires_login(self):
        self.client.delete_cookie(
            "sms_auth",
            path="/api",
        )

        response = self.client.get(
            self.url + "/faculties"
        )

        self.assertEqual(response.status_code, 401)

    def test_student_cannot_create_account(self):
        self.auth_service.current_user.return_value = (
            SimpleNamespace(role="Student")
        )

        response = self.client.post(
            self.url,
            json=STUDENT_DATA,
            headers=self.headers,
        )

        self.assertEqual(response.status_code, 403)
        self.create_service.create_record.assert_not_called()

    # =========================================
    # REQUEST SECURITY
    # =========================================

    def test_invalid_origin_rejected(self):
        response = self.client.post(
            self.url,
            json=STUDENT_DATA,
            headers={
                **self.headers,
                "Origin": "https://invalid.example",
            },
        )

        self.assertEqual(response.status_code, 403)
        self.create_service.create_record.assert_not_called()

    def test_invalid_csrf_rejected(self):
        response = self.client.post(
            self.url,
            json=STUDENT_DATA,
            headers={
                "Origin": "http://localhost:5173",
            },
        )

        self.assertEqual(response.status_code, 403)
        self.create_service.create_record.assert_not_called()

    # =========================================
    # MANUAL CREDENTIAL HANDOFF (NO SMTP)
    # =========================================

    def test_missing_notifier_does_not_block_creation(self):
        self._configure_creation_result()
        response = self.client.post(
            self.url, json=STUDENT_DATA, headers=self.headers
        )
        self.assertEqual(response.status_code, 201)
        self.create_service.create_record.assert_called_once()

    def test_create_account_returns_one_time_credentials(self):
        self._configure_creation_result()
        response = self.client.post(
            self.url, json=STUDENT_DATA, headers=self.headers
        )
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data["credentialDelivery"], "manual")
        self.assertEqual(data["account"]["studentId"], "STU0000004")
        self.assertEqual(
            data["initialCredentials"]["initialPassword"],
            "internal-test-password",
        )
        self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_registered_notifier_is_not_called(self):
        self._configure_creation_result()
        notifier = Mock()
        self.app.extensions["sms_account_notifier"] = notifier
        response = self.client.post(
            self.url, json=STUDENT_DATA, headers=self.headers
        )
        self.assertEqual(response.status_code, 201)
        notifier.deliver.assert_not_called()

    # =========================================
    # =========================================
    # VALIDATION ERRORS
    # =========================================

    def test_invalid_payload_returns_400(self):
        self._configure_creation_result()

        self.create_service.create_record.side_effect = (
            CreateAccountValidationError(
                "Full Name is required."
            )
        )

        response = self.client.post(
            self.url,
            json=STUDENT_DATA,
            headers=self.headers,
        )

        self.assertEqual(response.status_code, 400)

    def test_duplicate_username_returns_409(self):
        self._configure_creation_result()

        self.create_service.create_record.side_effect = (
            AccountAlreadyExistsError(
                "Username already exists."
            )
        )

        response = self.client.post(
            self.url,
            json=STUDENT_DATA,
            headers=self.headers,
        )

        self.assertEqual(response.status_code, 409)

    def test_invalid_major_returns_400(self):
        self._configure_creation_result()

        self.create_service.create_record.side_effect = (
            AccountReferenceError(
                "Selected major does not exist."
            )
        )

        response = self.client.post(
            self.url,
            json=STUDENT_DATA,
            headers=self.headers,
        )

        self.assertEqual(response.status_code, 400)

    def test_database_error_returns_503(self):
        self._configure_creation_result()

        self.create_service.create_record.side_effect = (
            RuntimeError("Simulated SQL failure")
        )

        response = self.client.post(
            self.url,
            json=STUDENT_DATA,
            headers=self.headers,
        )

        self.assertEqual(response.status_code, 503)


if __name__ == "__main__":
    unittest.main()
