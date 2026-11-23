
"""Tests for Group 05 Create Account Controller.

Use Case 11:
- Administrator-only access
- CSRF and Origin protection
- Faculty/Major options
- Input validation
- Error handling
- Notification after database commit
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

    def _enable_notifier(self):
        notifier = Mock()

        self.app.extensions[
            "sms_account_notifier"
        ] = notifier

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

        return notifier

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
    # DELIVERY PREREQUISITE
    # =========================================

    def test_missing_notifier_blocks_creation(self):
        response = self.client.post(
            self.url,
            json=STUDENT_DATA,
            headers=self.headers,
        )

        self.assertEqual(response.status_code, 503)
        self.create_service.create_record.assert_not_called()

    # =========================================
    # SUCCESS
    # =========================================

    def test_create_account_success(self):
        notifier = self._enable_notifier()

        response = self.client.post(
            self.url,
            json=STUDENT_DATA,
            headers=self.headers,
        )

        self.assertEqual(response.status_code, 201)

        result = response.get_json()

        self.assertEqual(
            result["account"]["studentId"],
            "STU0000004",
        )

        self.assertNotIn(
            "initialCredentials",
            result,
        )

        self.create_service.create_record.assert_called_once()
        notifier.deliver.assert_called_once()

    # =========================================
    # NOTIFICATION FAILURE
    # =========================================

    def test_notification_failure_is_not_reported_as_rollback(self):
        notifier = self._enable_notifier()

        notifier.deliver.side_effect = RuntimeError(
            "Delivery failed."
        )

        response = self.client.post(
            self.url,
            json=STUDENT_DATA,
            headers=self.headers,
        )

        self.assertEqual(response.status_code, 502)

        self.assertIn(
            "Account was created",
            response.get_json()["error"],
        )

    # =========================================
    # VALIDATION ERRORS
    # =========================================

    def test_invalid_payload_returns_400(self):
        self._enable_notifier()

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
        self._enable_notifier()

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
        self._enable_notifier()

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
        self._enable_notifier()

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
