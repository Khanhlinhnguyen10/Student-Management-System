
"""HTTP tests for Assign Lecturer API - Group 05.

Use Case 40.

The Assign Lecturer Blueprint must be registered
by create_app(), including in the test environment.

All business/database operations are mocked.
No real SQL Server changes are made.
"""

import unittest
from datetime import datetime, timezone
from unittest.mock import Mock

from app import create_app

from app.controllers.auth_security import (
    csrf_token_for_session,
)

from app.repositories.assign_lecturer_repository import (
    AssignmentBusyError,
    AssignmentNotFoundError,
    AssignmentScheduleConflictError,
)

from app.services.assign_lecturer_service import (
    AssignLecturerService,
    AssignLecturerValidationError,
)

from app.services.auth_service import AuthPrincipal


_ORIGIN = "http://localhost:5173"
_TOKEN = "t" * 43
_BASE = "/api/admin/assign-lecturer"

_VALID_PAYLOAD = {
    "classSectionId": "CLS0000005",
    "lecturerId": "LEC0000001",
}


class AdminAssignLecturerApiTests(unittest.TestCase):

    def setUp(self):
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "assign-lecturer-test-secret",
            "AUTH_ALLOWED_ORIGIN": _ORIGIN,
            "AUTH_COOKIE_SECURE": False,
        })

        # IMPORTANT:
        # Do NOT manually register the Blueprint here.
        # create_app() now registers it for all environments.

        self.service = Mock(
            spec=AssignLecturerService
        )

        self.app.extensions[
            "sms_assign_lecturer_service"
        ] = self.service

        self.auth_service = Mock()

        self.auth_service.current_user.return_value = (
            AuthPrincipal(
                user_id="USR000000001",
                username="testadmin",
                full_name="Test Administrator",
                role="Administrator",
                expires_at=datetime(
                    2030, 1, 1,
                    tzinfo=timezone.utc,
                ),
            )
        )

        self.app.extensions[
            "sms_auth_service"
        ] = self.auth_service

        self.client = self.app.test_client()

        self.client.set_cookie(
            "sms_auth",
            _TOKEN,
            path="/api",
        )

    def _post_headers(self, origin=_ORIGIN):
        with self.app.app_context():
            csrf_token = csrf_token_for_session(
                _TOKEN
            )

        return {
            "Origin": origin,
            "X-CSRF-Token": csrf_token,
        }

    def _assign(self):
        return self.client.post(
            f"{_BASE}/assign",
            json=_VALID_PAYLOAD,
            headers=self._post_headers(),
        )

    # =========================================
    # BLUEPRINT REGISTRATION
    # =========================================

    def test_blueprint_registered_by_create_app(self):
        self.assertIn(
            "admin_assign_lecturer",
            self.app.blueprints,
        )

        rules = {
            rule.rule
            for rule in self.app.url_map.iter_rules()
        }

        self.assertIn(
            f"{_BASE}/semesters",
            rules,
        )

        self.assertIn(
            f"{_BASE}/sections",
            rules,
        )

        self.assertIn(
            f"{_BASE}/lecturers",
            rules,
        )

        self.assertIn(
            f"{_BASE}/assign",
            rules,
        )

    # =========================================
    # GET SEMESTERS
    # =========================================

    def test_get_semesters(self):
        expected = [
            {
                "semesterId": "SEM0000001",
                "semesterName": "Semester 1",
            }
        ]

        self.service.list_semesters.return_value = (
            expected
        )

        response = self.client.get(
            f"{_BASE}/semesters"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.get_json()["items"],
            expected,
        )

    # =========================================
    # GET LECTURERS
    # =========================================

    def test_get_lecturers(self):
        expected = [
            {
                "lecturerId": "LEC0000001",
                "fullName": "Test Lecturer",
            }
        ]

        self.service.list_lecturers.return_value = (
            expected
        )

        response = self.client.get(
            f"{_BASE}/lecturers"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.get_json()["items"],
            expected,
        )

    # =========================================
    # GET CLASS SECTIONS
    # =========================================

    def test_get_sections_by_semester(self):
        self.service.list_sections.return_value = []

        response = self.client.get(
            f"{_BASE}/sections?semesterId=SEM0000001"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.service.list_sections.assert_called_once_with(
            "SEM0000001"
        )

    def test_get_sections_missing_semester(self):
        self.service.list_sections.side_effect = (
            AssignLecturerValidationError(
                "Semester ID is required."
            )
        )

        response = self.client.get(
            f"{_BASE}/sections"
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    # =========================================
    # SUCCESSFUL ASSIGNMENT
    # =========================================

    def test_assign_success(self):
        expected = {
            "classSectionId": "CLS0000005",
            "classCode": "TEST.01",
            "semesterId": "SEM0000001",
            "lecturerId": "LEC0000001",
            "changed": True,
        }

        self.service.assign_record.return_value = (
            expected
        )

        response = self._assign()

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.get_json()["assignment"],
            expected,
        )

        self.service.assign_record.assert_called_once_with(
            _VALID_PAYLOAD
        )

    # =========================================
    # SCHEDULE CONFLICT
    # =========================================

    def test_assign_conflict(self):
        self.service.assign_record.side_effect = (
            AssignmentScheduleConflictError(
                "Teaching schedule conflict with TEST.02, "
                "day 2, 08:00-10:00."
            )
        )

        response = self._assign()

        self.assertEqual(
            response.status_code,
            409,
        )

        self.assertIn(
            "TEST.02",
            response.get_json()["error"],
        )

    # =========================================
    # RECORD NOT FOUND
    # =========================================

    def test_assign_not_found(self):
        self.service.assign_record.side_effect = (
            AssignmentNotFoundError(
                "Lecturer does not exist."
            )
        )

        response = self._assign()

        self.assertEqual(
            response.status_code,
            404,
        )

    # =========================================
    # INVALID INPUT
    # =========================================

    def test_assign_invalid_payload(self):
        self.service.assign_record.side_effect = (
            AssignLecturerValidationError(
                "Lecturer ID is required."
            )
        )

        response = self._assign()

        self.assertEqual(
            response.status_code,
            400,
        )

    # =========================================
    # MISSING CSRF
    # =========================================

    def test_assign_without_csrf_rejected(self):
        response = self.client.post(
            f"{_BASE}/assign",
            json=_VALID_PAYLOAD,
            headers={
                "Origin": _ORIGIN,
            },
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.service.assign_record.assert_not_called()

    # =========================================
    # UNAPPROVED ORIGIN
    # =========================================

    def test_assign_wrong_origin_rejected(self):
        response = self.client.post(
            f"{_BASE}/assign",
            json=_VALID_PAYLOAD,
            headers=self._post_headers(
                origin="https://untrusted.example"
            ),
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.service.assign_record.assert_not_called()

    # =========================================
    # ROLE-BASED ACCESS CONTROL
    # =========================================

    def test_student_cannot_assign(self):
        self.auth_service.current_user.return_value = (
            AuthPrincipal(
                user_id="USR000000002",
                username="teststudent",
                full_name="Test Student",
                role="Student",
                expires_at=datetime(
                    2030, 1, 1,
                    tzinfo=timezone.utc,
                ),
            )
        )

        response = self._assign()

        self.assertEqual(
            response.status_code,
            403,
        )

        self.service.assign_record.assert_not_called()

    # =========================================
    # TRANSACTION BUSY
    # =========================================

    def test_assign_busy(self):
        self.service.assign_record.side_effect = (
            AssignmentBusyError(
                "Assignment is busy. Please try again."
            )
        )

        response = self._assign()

        self.assertEqual(
            response.status_code,
            503,
        )


if __name__ == "__main__":
    unittest.main()
