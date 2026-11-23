
"""HTTP and Service tests for Group 05 Use Cases 13, 14 and 15."""

from datetime import date, datetime, timezone
import unittest
from unittest.mock import Mock

from app import create_app

from app.controllers.auth_security import (
    SESSION_COOKIE_NAME,
    csrf_token_for_session,
)

from app.repositories.student_repository import (
    StudentRecord,
    StudentDuplicateCitizenIdError,
    StudentDataIntegrityError,
)

from app.services.admin_student_service import (
    AdminStudentService,
    StudentNotFoundError,
    StudentValidationError,
)

from app.services.auth_service import (
    AuthPrincipal,
    SessionExpiredError,
)


_TEST_TOKEN = "t" * 43

_TEST_EXPIRY = datetime(
    2026, 11, 15, 10, 15,
    tzinfo=timezone.utc,
)

_TEST_STUDENT = StudentRecord(
    studentId="STU0000001",
    citizenId="079000000002",
    fullName="Tran Minh Anh",
    dateOfBirth=date(2005, 3, 12),
    email="student01@example.test",
    gender="Female",
    phoneNumber="0900000002",
    facultyName="Information Technology",
    majorName="Computer Science",
    academicStatus="Active",
)


def _valid_update_payload():
    """Return a valid student update request."""

    return {
        "citizenId": "079000000002",
        "fullName": "Tran Minh Anh Updated",
        "dateOfBirth": "2005-03-12",
        "email": "student01@example.test",
        "gender": "Female",
        "phoneNumber": "0900000002",
        "majorId": "MAJ0000001",
        "academicStatus": "Active",
    }


# =====================================================
# ADMIN STUDENT API TESTS
# =====================================================

class AdminStudentApiTests(unittest.TestCase):

    def setUp(self):

        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "test-only-secret",
            "AUTH_ALLOWED_ORIGIN": "http://localhost:5173",
        })

        # Mock authentication service.
        self.auth = Mock()

        self.auth.current_user.return_value = AuthPrincipal(
            user_id="USR000000001",
            username="admin01",
            full_name="Example Admin",
            role="Administrator",
            expires_at=_TEST_EXPIRY,
        )

        self.app.extensions[
            "sms_auth_service"
        ] = self.auth

        # Mock student application service.
        self.student_service = Mock()

        self.student_service.list_records.return_value = {
            "items": [
                {
                    "studentId": "STU0000001",
                    "fullName": "Tran Minh Anh",
                    "academicStatus": "Active",
                }
            ],
            "total": 1,
            "limit": 10,
            "offset": 0,
        }

        self.student_service.get_record.return_value = {
            "studentId": "STU0000001",
            "fullName": "Tran Minh Anh",
            "academicStatus": "Active",
        }

        self.student_service.update_record.return_value = {
            "studentId": "STU0000001",
            "fullName": "Tran Minh Anh Updated",
            "academicStatus": "Active",
        }

        self.student_service.delete_record.return_value = True

        self.app.extensions[
            "sms_admin_student_service"
        ] = self.student_service

        self.client = self.app.test_client()

    # -------------------------------------------------
    # TEST HELPERS
    # -------------------------------------------------

    def _auth_cookie(self):

        self.client.set_cookie(
            SESSION_COOKIE_NAME,
            _TEST_TOKEN,
            path="/api",
        )

    def _write_headers(self):
        """Generate the real session-bound CSRF token."""

        with self.app.app_context():
            token = csrf_token_for_session(
                _TEST_TOKEN
            )

        return {
            "Origin": "http://localhost:5173",
            "X-CSRF-Token": token,
        }

    # -------------------------------------------------
    # USE CASE 13 - VIEW STUDENT RECORDS
    # -------------------------------------------------

    def test_unauthenticated_list_is_rejected(self):

        result = self.client.get(
            "/api/admin/students",
        )

        self.assertEqual(
            result.status_code,
            401,
        )

        self.student_service.list_records.assert_not_called()

    def test_unauthenticated_detail_is_rejected(self):

        result = self.client.get(
            "/api/admin/students/STU0000001",
        )

        self.assertEqual(
            result.status_code,
            401,
        )

    def test_student_role_cannot_read_all_students(self):

        self._auth_cookie()

        self.auth.current_user.return_value = AuthPrincipal(
            user_id="USR000000002",
            username="student01",
            full_name="Tran Minh Anh",
            role="Student",
            expires_at=_TEST_EXPIRY,
        )

        result = self.client.get(
            "/api/admin/students",
        )

        self.assertEqual(
            result.status_code,
            403,
        )

        self.student_service.list_records.assert_not_called()

    def test_admin_lists_students_and_protects_cache(self):

        self._auth_cookie()

        result = self.client.get(
            "/api/admin/students?limit=10&offset=0",
        )

        self.assertEqual(
            result.status_code,
            200,
        )

        self.assertEqual(
            result.json["total"],
            1,
        )

        self.assertEqual(
            result.headers["Cache-Control"],
            "no-store",
        )

        self.student_service.list_records.assert_called_once_with(
            limit=10,
            offset=0,
            search="",
        )

    def test_search_is_sent_as_plain_parameter(self):

        self._auth_cookie()

        result = self.client.get(
            "/api/admin/students?search=Tran%20Minh&limit=5",
        )

        self.assertEqual(
            result.status_code,
            200,
        )

        self.student_service.list_records.assert_called_once_with(
            limit=5,
            offset=0,
            search="Tran Minh",
        )

    def test_admin_reads_student_details(self):

        self._auth_cookie()

        result = self.client.get(
            "/api/admin/students/STU0000001",
        )

        self.assertEqual(
            result.status_code,
            200,
        )

        self.assertEqual(
            result.json["student"]["studentId"],
            "STU0000001",
        )

        self.student_service.get_record.assert_called_once_with(
            "STU0000001",
        )

    def test_missing_student_gives_404(self):

        self._auth_cookie()

        self.student_service.get_record.side_effect = (
            StudentNotFoundError()
        )

        result = self.client.get(
            "/api/admin/students/STU0000099",
        )

        self.assertEqual(
            result.status_code,
            404,
        )

    def test_invalid_page_is_rejected_without_database(self):

        self._auth_cookie()

        urls = (
            "/api/admin/students?limit=0",
            "/api/admin/students?limit=999",
            "/api/admin/students?offset=-1",
            "/api/admin/students?offset=3.2",
        )

        for url in urls:

            with self.subTest(url=url):

                result = self.client.get(url)

                self.assertEqual(
                    result.status_code,
                    400,
                )

        self.student_service.list_records.assert_not_called()

    def test_database_failure_returns_sanitized_error(self):

        self._auth_cookie()

        self.student_service.list_records.side_effect = (
            RuntimeError("PRIVATE_SQL_ERROR")
        )

        result = self.client.get(
            "/api/admin/students",
        )

        self.assertEqual(
            result.status_code,
            503,
        )

        self.assertNotIn(
            "PRIVATE_SQL_ERROR",
            str(result.json),
        )

    def test_expired_session_returns_401(self):

        self._auth_cookie()

        self.auth.current_user.side_effect = (
            SessionExpiredError("Expired")
        )

        result = self.client.get(
            "/api/admin/students",
        )

        self.assertEqual(
            result.status_code,
            401,
        )

        self.student_service.list_records.assert_not_called()

    # -------------------------------------------------
    # USE CASE 14 - UPDATE STUDENT RECORDS
    # -------------------------------------------------

    def test_unauthenticated_update_is_rejected(self):

        result = self.client.put(
            "/api/admin/students/STU0000001",
            json=_valid_update_payload(),
            headers=self._write_headers(),
        )

        self.assertEqual(
            result.status_code,
            401,
        )

        self.student_service.update_record.assert_not_called()

    def test_admin_updates_student(self):

        self._auth_cookie()

        payload = _valid_update_payload()

        result = self.client.put(
            "/api/admin/students/STU0000001",
            json=payload,
            headers=self._write_headers(),
        )

        self.assertEqual(
            result.status_code,
            200,
        )

        self.assertEqual(
            result.json["message"],
            "Student record updated successfully.",
        )

        self.assertEqual(
            result.json["student"]["fullName"],
            "Tran Minh Anh Updated",
        )

        self.student_service.update_record.assert_called_once_with(
            "STU0000001",
            payload,
        )

    def test_update_rejects_missing_csrf(self):

        self._auth_cookie()

        result = self.client.put(
            "/api/admin/students/STU0000001",
            json=_valid_update_payload(),
            headers={
                "Origin": "http://localhost:5173",
            },
        )

        self.assertEqual(
            result.status_code,
            403,
        )

        self.student_service.update_record.assert_not_called()

    def test_update_rejects_unapproved_origin(self):

        self._auth_cookie()

        headers = self._write_headers()

        headers["Origin"] = "http://malicious.example"

        result = self.client.put(
            "/api/admin/students/STU0000001",
            json=_valid_update_payload(),
            headers=headers,
        )

        self.assertEqual(
            result.status_code,
            403,
        )

        self.student_service.update_record.assert_not_called()

    def test_update_requires_json(self):

        self._auth_cookie()

        result = self.client.put(
            "/api/admin/students/STU0000001",
            data="invalid body",
            content_type="text/plain",
            headers=self._write_headers(),
        )

        self.assertEqual(
            result.status_code,
            415,
        )

        self.student_service.update_record.assert_not_called()

    def test_update_duplicate_citizen_id_returns_409(self):

        self._auth_cookie()

        self.student_service.update_record.side_effect = (
            StudentDuplicateCitizenIdError(
                "Citizen ID Number already exists."
            )
        )

        result = self.client.put(
            "/api/admin/students/STU0000001",
            json=_valid_update_payload(),
            headers=self._write_headers(),
        )

        self.assertEqual(
            result.status_code,
            409,
        )

    def test_update_integrity_error_returns_409(self):

        self._auth_cookie()

        self.student_service.update_record.side_effect = (
            StudentDataIntegrityError(
                "The selected major is invalid."
            )
        )

        result = self.client.put(
            "/api/admin/students/STU0000001",
            json=_valid_update_payload(),
            headers=self._write_headers(),
        )

        self.assertEqual(
            result.status_code,
            409,
        )

    def test_student_role_cannot_update_student(self):

        self._auth_cookie()

        self.auth.current_user.return_value = AuthPrincipal(
            user_id="USR000000002",
            username="student01",
            full_name="Tran Minh Anh",
            role="Student",
            expires_at=_TEST_EXPIRY,
        )

        result = self.client.put(
            "/api/admin/students/STU0000001",
            json=_valid_update_payload(),
            headers=self._write_headers(),
        )

        self.assertEqual(
            result.status_code,
            403,
        )

        self.student_service.update_record.assert_not_called()

    # -------------------------------------------------
    # USE CASE 15 - DELETE STUDENT RECORDS
    # -------------------------------------------------

    def test_unauthenticated_delete_is_rejected(self):

        result = self.client.delete(
            "/api/admin/students/STU0000001",
            headers=self._write_headers(),
        )

        self.assertEqual(
            result.status_code,
            401,
        )

        self.student_service.delete_record.assert_not_called()

    def test_admin_deletes_student(self):

        self._auth_cookie()

        result = self.client.delete(
            "/api/admin/students/STU0000001",
            headers=self._write_headers(),
        )

        self.assertEqual(
            result.status_code,
            200,
        )

        self.assertEqual(
            result.json["message"],
            "Student record deleted successfully.",
        )

        self.student_service.delete_record.assert_called_once_with(
            "STU0000001",
        )

    def test_delete_rejects_missing_csrf(self):

        self._auth_cookie()

        result = self.client.delete(
            "/api/admin/students/STU0000001",
            headers={
                "Origin": "http://localhost:5173",
            },
        )

        self.assertEqual(
            result.status_code,
            403,
        )

        self.student_service.delete_record.assert_not_called()

    def test_delete_rejects_unapproved_origin(self):

        self._auth_cookie()

        headers = self._write_headers()

        headers["Origin"] = "http://malicious.example"

        result = self.client.delete(
            "/api/admin/students/STU0000001",
            headers=headers,
        )

        self.assertEqual(
            result.status_code,
            403,
        )

        self.student_service.delete_record.assert_not_called()

    def test_delete_rejects_related_records(self):

        self._auth_cookie()

        self.student_service.delete_record.side_effect = (
            StudentDataIntegrityError(
                "Student has related records."
            )
        )

        result = self.client.delete(
            "/api/admin/students/STU0000001",
            headers=self._write_headers(),
        )

        self.assertEqual(
            result.status_code,
            409,
        )

    def test_delete_missing_student_returns_404(self):

        self._auth_cookie()

        self.student_service.delete_record.side_effect = (
            StudentNotFoundError()
        )

        result = self.client.delete(
            "/api/admin/students/STU0000099",
            headers=self._write_headers(),
        )

        self.assertEqual(
            result.status_code,
            404,
        )

    def test_delete_database_failure_returns_sanitized_error(self):

        self._auth_cookie()

        self.student_service.delete_record.side_effect = (
            RuntimeError("PRIVATE_DELETE_SQL_ERROR")
        )

        result = self.client.delete(
            "/api/admin/students/STU0000001",
            headers=self._write_headers(),
        )

        self.assertEqual(
            result.status_code,
            503,
        )

        self.assertNotIn(
            "PRIVATE_DELETE_SQL_ERROR",
            str(result.json),
        )


# =====================================================
# ADMIN STUDENT SERVICE TESTS
# =====================================================

class AdminStudentServiceTests(unittest.TestCase):

    def setUp(self):

        self.repo = Mock()

        self.repo.list_students.return_value = [
            _TEST_STUDENT,
        ]

        self.repo.count_students.return_value = 1

        self.repo.get_student_by_id.return_value = (
            _TEST_STUDENT
        )

        self.repo.update_student.return_value = (
            _TEST_STUDENT
        )

        self.repo.delete_student.return_value = True

        self.service = AdminStudentService(
            repository=self.repo,
        )

    # -------------------------------------------------
    # VIEW TESTS
    # -------------------------------------------------

    def test_list_result_has_iso_date_and_total(self):

        result = self.service.list_records(
            limit=10,
            offset=0,
            search="Tran",
        )

        self.assertEqual(
            result["total"],
            1,
        )

        self.assertEqual(
            result["items"][0]["dateOfBirth"],
            "2005-03-12",
        )

        self.repo.list_students.assert_called_once_with(
            limit=10,
            offset=0,
            search="Tran",
        )

    def test_detail_serializes_student_record(self):

        data = self.service.get_record(
            "STU0000001",
        )

        self.assertEqual(
            data["fullName"],
            "Tran Minh Anh",
        )

        self.assertEqual(
            data["academicStatus"],
            "Active",
        )

    def test_missing_student_raises_domain_error(self):

        self.repo.get_student_by_id.return_value = None

        with self.assertRaises(
            StudentNotFoundError
        ):
            self.service.get_record(
                "STU0000099",
            )

    # -------------------------------------------------
    # UPDATE TESTS
    # -------------------------------------------------

    def test_update_record_serializes_student(self):

        payload = _valid_update_payload()

        result = self.service.update_record(
            "STU0000001",
            payload,
        )

        self.assertEqual(
            result["studentId"],
            "STU0000001",
        )

        self.assertEqual(
            result["dateOfBirth"],
            "2005-03-12",
        )

        self.repo.update_student.assert_called_once_with(
            student_id="STU0000001",
            citizen_id="079000000002",
            full_name="Tran Minh Anh Updated",
            date_of_birth=date(2005, 3, 12),
            email="student01@example.test",
            gender="Female",
            phone_number="0900000002",
            major_id="MAJ0000001",
            academic_status="Active",
        )

    def test_update_rejects_student_id_modification(self):

        payload = _valid_update_payload()

        payload["studentId"] = "STU0000099"

        with self.assertRaises(
            StudentValidationError
        ):
            self.service.update_record(
                "STU0000001",
                payload,
            )

        self.repo.update_student.assert_not_called()

    def test_update_rejects_missing_required_fields(self):

        payload = {
            "fullName": "Tran Minh Anh",
        }

        with self.assertRaises(
            StudentValidationError
        ):
            self.service.update_record(
                "STU0000001",
                payload,
            )

        self.repo.update_student.assert_not_called()

    def test_update_missing_student_raises_domain_error(self):

        self.repo.update_student.return_value = None

        with self.assertRaises(
            StudentNotFoundError
        ):
            self.service.update_record(
                "STU0000001",
                _valid_update_payload(),
            )

    # -------------------------------------------------
    # DELETE TESTS
    # -------------------------------------------------

    def test_delete_record_returns_true(self):

        result = self.service.delete_record(
            "STU0000001",
        )

        self.assertTrue(result)

        self.repo.delete_student.assert_called_once_with(
            "STU0000001",
        )

    def test_delete_missing_student_raises_domain_error(self):

        self.repo.delete_student.return_value = False

        with self.assertRaises(
            StudentNotFoundError
        ):
            self.service.delete_record(
                "STU0000099",
            )


if __name__ == "__main__":
    unittest.main()
