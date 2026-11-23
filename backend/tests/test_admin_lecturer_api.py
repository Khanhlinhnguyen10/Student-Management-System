
"""HTTP tests for Administrator Lecturer Management - Group 05."""

from datetime import datetime, timezone
import unittest
from unittest.mock import Mock

from app import create_app

from app.controllers.auth_security import (
    csrf_token_for_session,
)

from app.repositories.admin_lecturer_repository import (
    LecturerDataIntegrityError,
    LecturerDuplicateIdentityError,
)

from app.services.admin_lecturer_service import (
    LecturerNotFoundError,
    LecturerValidationError,
)

from app.services.auth_service import AuthPrincipal


TOKEN = "t" * 43
ORIGIN = "http://localhost:5173"

LECTURER = {
    "lecturerId": "LEC0000001",
    "citizenId": "079000000001",
    "fullName": "Test Lecturer",
    "dateOfBirth": "1985-05-10",
    "email": "lecturer@example.test",
    "gender": "Female",
    "phoneNumber": "0900000001",
    "facultyId": "FAC0000001",
    "facultyName": "Information Technology",
}


class AdminLecturerApiTests(unittest.TestCase):

    def setUp(self):
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "test-only-secret",
            "AUTH_ALLOWED_ORIGIN": ORIGIN,
        })

        self.auth = Mock()
        self.auth.current_user.return_value = AuthPrincipal(
            user_id="USR000000001",
            username="admin01",
            full_name="Test Administrator",
            role="Administrator",
            expires_at=datetime(
                2026, 11, 18, 12, 0,
                tzinfo=timezone.utc,
            ),
        )

        self.app.extensions["sms_auth_service"] = self.auth

        self.service = Mock()

        self.service.list_records.return_value = {
            "items": [LECTURER],
            "total": 1,
            "limit": 10,
            "offset": 0,
        }

        self.service.get_record.return_value = LECTURER

        self.service.list_faculty_options.return_value = [
            {
                "facultyId": "FAC0000001",
                "facultyName": "Information Technology",
            }
        ]

        self.service.update_record.return_value = LECTURER
        self.service.delete_record.return_value = True

        self.app.extensions[
            "sms_admin_lecturer_service"
        ] = self.service

        self.client = self.app.test_client()

    def authenticate(self):
        self.client.set_cookie(
            "sms_auth",
            TOKEN,
            path="/api",
        )

    def write_headers(self):
        with self.app.app_context():
            csrf = csrf_token_for_session(TOKEN)

        return {
            "Origin": ORIGIN,
            "X-CSRF-Token": csrf,
        }

    def test_unauthenticated_list_rejected(self):
        response = self.client.get(
            "/api/admin/lecturers"
        )

        self.assertEqual(response.status_code, 401)

    def test_student_cannot_read_lecturers(self):
        self.authenticate()

        self.auth.current_user.return_value = AuthPrincipal(
            user_id="USR000000002",
            username="student01",
            full_name="Test Student",
            role="Student",
            expires_at=datetime.now(timezone.utc),
        )

        response = self.client.get(
            "/api/admin/lecturers"
        )

        self.assertEqual(response.status_code, 403)

    def test_admin_can_list_lecturers(self):
        self.authenticate()

        response = self.client.get(
            "/api/admin/lecturers"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["total"], 1)

    def test_invalid_pagination_rejected(self):
        self.authenticate()

        response = self.client.get(
            "/api/admin/lecturers?limit=0"
        )

        self.assertEqual(response.status_code, 400)
        self.service.list_records.assert_not_called()

    def test_admin_can_view_details(self):
        self.authenticate()

        response = self.client.get(
            "/api/admin/lecturers/LEC0000001"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json["lecturer"]["lecturerId"],
            "LEC0000001",
        )

    def test_faculty_options_available(self):
        self.authenticate()

        response = self.client.get(
            "/api/admin/lecturers/faculties"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            len(response.json["items"]),
            1,
        )

    def test_update_requires_csrf(self):
        self.authenticate()

        response = self.client.put(
            "/api/admin/lecturers/LEC0000001",
            json={
                "citizenId": "079000000001",
                "fullName": "Test Lecturer",
                "facultyId": "FAC0000001",
            },
            headers={"Origin": ORIGIN},
        )

        self.assertEqual(response.status_code, 403)
        self.service.update_record.assert_not_called()

    def test_admin_can_update_lecturer(self):
        self.authenticate()

        payload = {
            "citizenId": "079000000001",
            "fullName": "Test Lecturer",
            "facultyId": "FAC0000001",
        }

        response = self.client.put(
            "/api/admin/lecturers/LEC0000001",
            json=payload,
            headers=self.write_headers(),
        )

        self.assertEqual(response.status_code, 200)

        self.service.update_record.assert_called_once_with(
            "LEC0000001",
            payload,
        )

    def test_duplicate_identity_returns_conflict(self):
        self.authenticate()

        self.service.update_record.side_effect = (
            LecturerDuplicateIdentityError(
                "Citizen ID already exists."
            )
        )

        response = self.client.put(
            "/api/admin/lecturers/LEC0000001",
            json={
                "citizenId": "079000000001",
                "fullName": "Test Lecturer",
                "facultyId": "FAC0000001",
            },
            headers=self.write_headers(),
        )

        self.assertEqual(response.status_code, 409)

    def test_missing_lecturer_returns_404(self):
        self.authenticate()

        self.service.get_record.side_effect = (
            LecturerNotFoundError(
                "Lecturer record not found."
            )
        )

        response = self.client.get(
            "/api/admin/lecturers/LEC9999999"
        )

        self.assertEqual(response.status_code, 404)

    def test_delete_requires_csrf(self):
        self.authenticate()

        response = self.client.delete(
            "/api/admin/lecturers/LEC0000001",
            headers={"Origin": ORIGIN},
        )

        self.assertEqual(response.status_code, 403)
        self.service.delete_record.assert_not_called()

    def test_admin_can_delete_lecturer(self):
        self.authenticate()

        response = self.client.delete(
            "/api/admin/lecturers/LEC0000001",
            headers=self.write_headers(),
        )

        self.assertEqual(response.status_code, 200)

        self.service.delete_record.assert_called_once_with(
            "LEC0000001"
        )

    def test_assigned_lecturer_cannot_be_deleted(self):
        self.authenticate()

        self.service.delete_record.side_effect = (
            LecturerDataIntegrityError(
                "Lecturer is assigned to a class."
            )
        )

        response = self.client.delete(
            "/api/admin/lecturers/LEC0000001",
            headers=self.write_headers(),
        )

        self.assertEqual(response.status_code, 409)


if __name__ == "__main__":
    unittest.main()
