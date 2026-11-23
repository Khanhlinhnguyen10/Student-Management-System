
"""Lecturer Gradebook controller API tests.

Uses Flask test client and a mocked service.
Does not connect to the real SQL Server.
"""

import hashlib
import inspect
import unittest

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from flask import Flask, g

from app.controllers import lecturer_sections_controller as controller
from app.controllers.auth_security import SESSION_COOKIE_NAME


USER_ID = "USR0000901"
OWN_SECTION_ID = "CLS0000901"
OTHER_SECTION_ID = "CLS0000914"
ENROLLMENT_ID = "ENR0000906"
RAW_TOKEN = "unit-test-lecturer-session"

MARKS = {
    "midtermMark": 8.0,
    "assignmentMark": None,
    "attendanceMark": None,
    "finalExamMark": None,
}

FINAL_MARKS = {
    "midtermMark": 8.0,
    "assignmentMark": 8.0,
    "attendanceMark": 9.0,
    "finalExamMark": 8.0,
}


class TestLecturerGradebookApiPermissions(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__)
        self.app.config["TESTING"] = True

        self.app.register_blueprint(
            controller.lecturer_sections_bp,
            url_prefix="/api/lecturer",
        )

        # Isolate controller behavior from the role
        # authentication decorator. Authentication itself
        # must be tested separately.
        for name in (
            "get_section_gradebook",
            "save_gradebook_draft",
            "save_final_grade",
        ):
            endpoint = f"lecturer_sections.{name}"

            decorated_view = self.app.view_functions[endpoint]
            unwrapped_view = inspect.unwrap(decorated_view)

            if decorated_view is unwrapped_view:
                raise AssertionError(
                    "Cannot isolate roles_required: "
                    "the decorator does not expose __wrapped__."
                )

            self.app.view_functions[endpoint] = unwrapped_view

        @self.app.before_request
        def inject_test_lecturer():
            g.auth_principal = SimpleNamespace(
                user_id=USER_ID,
            )

        self.service = MagicMock()

        self.app.extensions[
            "sms_lecturer_gradebook_service"
        ] = self.service

        self.client = self.app.test_client()
        self.client.set_cookie(
            SESSION_COOKIE_NAME,
            RAW_TOKEN,
        )

        origin_patcher = patch.object(
            controller,
            "request_has_approved_origin",
            return_value=True,
        )

        csrf_patcher = patch.object(
            controller,
            "validate_csrf",
            return_value=True,
        )

        self.origin_check = origin_patcher.start()
        self.csrf_check = csrf_patcher.start()

        self.addCleanup(origin_patcher.stop)
        self.addCleanup(csrf_patcher.stop)

    @staticmethod
    def gradebook_url(section_id, enrollment_id):
        return (
            f"/api/lecturer/sections/{section_id}"
            f"/gradebook/{enrollment_id}"
        )

    @staticmethod
    def finalize_url(section_id, enrollment_id):
        return (
            f"/api/lecturer/sections/{section_id}"
            f"/gradebook/{enrollment_id}/finalize"
        )

    def test_get_assigned_gradebook_success(self):
        self.service.get_section_gradebook.return_value = {
            "section": {
                "classSectionId": OWN_SECTION_ID,
            },
            "students": [],
        }

        response = self.client.get(
            f"/api/lecturer/sections/"
            f"{OWN_SECTION_ID}/gradebook"
        )

        self.assertEqual(response.status_code, 200)

        self.assertIn("section", response.get_json())

        self.service.get_section_gradebook.assert_called_once_with(
            USER_ID,
            OWN_SECTION_ID,
        )

    def test_get_unassigned_gradebook_returns_404(self):
        self.service.get_section_gradebook.return_value = None

        response = self.client.get(
            f"/api/lecturer/sections/"
            f"{OTHER_SECTION_ID}/gradebook"
        )

        self.assertEqual(response.status_code, 404)

        self.assertNotIn(
            "students",
            response.get_json(),
        )

    def test_save_draft_success(self):
        self.service.save_draft.return_value = {
            "gradebookId": "GRB0000906",
            "isFinalized": False,
        }

        response = self.client.put(
            self.gradebook_url(
                OWN_SECTION_ID,
                ENROLLMENT_ID,
            ),
            json=MARKS,
        )

        self.assertEqual(response.status_code, 200)

        self.assertFalse(
            response.get_json()["gradebook"]["isFinalized"]
        )

        self.service.save_draft.assert_called_once_with(
            USER_ID,
            OWN_SECTION_ID,
            ENROLLMENT_ID,
            MARKS,
        )

    def test_save_draft_other_class_returns_404(self):
        self.service.save_draft.side_effect = LookupError(
            "Enrollment not found in assigned class."
        )

        response = self.client.put(
            self.gradebook_url(
                OTHER_SECTION_ID,
                ENROLLMENT_ID,
            ),
            json=MARKS,
        )

        self.assertEqual(response.status_code, 404)

        self.assertEqual(
            response.get_json()["error"],
            "Enrollment not found.",
        )

    def test_finalize_other_class_returns_404(self):
        self.service.save_final.side_effect = LookupError(
            "Enrollment not found in assigned class."
        )

        response = self.client.put(
            self.finalize_url(
                OTHER_SECTION_ID,
                ENROLLMENT_ID,
            ),
            json=FINAL_MARKS,
        )

        self.assertEqual(response.status_code, 404)

        self.assertEqual(
            response.get_json()["error"],
            "Enrollment not found in assigned class.",
        )

    def test_draft_finalized_record_returns_409(self):
        self.service.save_draft.side_effect = PermissionError(
            "Cannot save a draft over finalized grades."
        )

        response = self.client.put(
            self.gradebook_url(
                OWN_SECTION_ID,
                ENROLLMENT_ID,
            ),
            json=MARKS,
        )

        self.assertEqual(response.status_code, 409)

    def test_finalize_finalized_record_returns_409(self):
        self.service.save_final.side_effect = PermissionError(
            "Cannot modify finalized grades."
        )

        response = self.client.put(
            self.finalize_url(
                OWN_SECTION_ID,
                ENROLLMENT_ID,
            ),
            json=FINAL_MARKS,
        )

        self.assertEqual(response.status_code, 409)

        self.assertEqual(
            response.get_json()["error"],
            "Finalized grades cannot be modified.",
        )

    def test_invalid_lecturer_session_returns_401(self):
        self.service.save_final.side_effect = PermissionError(
            "Active Lecturer session required."
        )

        response = self.client.put(
            self.finalize_url(
                OWN_SECTION_ID,
                ENROLLMENT_ID,
            ),
            json=FINAL_MARKS,
        )

        self.assertEqual(response.status_code, 401)

    def test_finalize_success(self):
        self.service.save_final.return_value = {
            "gradebookId": "GRB0000906",
            "finalScore": 8.1,
            "letterGrade": "B+",
            "isFinalized": True,
        }

        response = self.client.put(
            self.finalize_url(
                OWN_SECTION_ID,
                ENROLLMENT_ID,
            ),
            json=FINAL_MARKS,
        )

        self.assertEqual(response.status_code, 200)

        self.assertTrue(
            response.get_json()["gradebook"]["isFinalized"]
        )

        expected_hash = hashlib.sha256(
            RAW_TOKEN.encode("ascii")
        ).hexdigest()

        self.service.save_final.assert_called_once_with(
            USER_ID,
            expected_hash,
            OWN_SECTION_ID,
            ENROLLMENT_ID,
            FINAL_MARKS,
        )

    def test_invalid_csrf_returns_403(self):
        self.csrf_check.return_value = False

        response = self.client.put(
            self.gradebook_url(
                OWN_SECTION_ID,
                ENROLLMENT_ID,
            ),
            json=MARKS,
        )

        self.assertEqual(response.status_code, 403)

        self.service.save_draft.assert_not_called()

    def test_missing_session_cookie_returns_403(self):
        self.client.delete_cookie(SESSION_COOKIE_NAME)

        response = self.client.put(
            self.gradebook_url(
                OWN_SECTION_ID,
                ENROLLMENT_ID,
            ),
            json=MARKS,
        )

        self.assertEqual(response.status_code, 403)

        self.service.save_draft.assert_not_called()

    def test_invalid_origin_returns_403(self):
        self.origin_check.return_value = False

        response = self.client.put(
            self.gradebook_url(
                OWN_SECTION_ID,
                ENROLLMENT_ID,
            ),
            json=MARKS,
        )

        self.assertEqual(response.status_code, 403)

        self.service.save_draft.assert_not_called()

    def test_non_json_request_returns_415(self):
        response = self.client.put(
            self.gradebook_url(
                OWN_SECTION_ID,
                ENROLLMENT_ID,
            ),
            data="invalid payload",
            content_type="text/plain",
        )

        self.assertEqual(response.status_code, 415)

        self.service.save_draft.assert_not_called()

    def test_json_array_returns_400(self):
        response = self.client.put(
            self.gradebook_url(
                OWN_SECTION_ID,
                ENROLLMENT_ID,
            ),
            json=[8, 9, 7, 8],
        )

        self.assertEqual(response.status_code, 400)

        self.service.save_draft.assert_not_called()

    def test_grade_validation_error_returns_400(self):
        self.service.save_draft.side_effect = ValueError(
            "Invalid grade value."
        )

        response = self.client.put(
            self.gradebook_url(
                OWN_SECTION_ID,
                ENROLLMENT_ID,
            ),
            json=MARKS,
        )

        self.assertEqual(response.status_code, 400)

    def test_large_request_returns_413(self):
        response = self.client.put(
            self.gradebook_url(
                OWN_SECTION_ID,
                ENROLLMENT_ID,
            ),
            data="x" * 5000,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 413)

        self.service.save_draft.assert_not_called()

    def test_gradebook_response_disables_cache(self):
        self.service.get_section_gradebook.return_value = None

        response = self.client.get(
            f"/api/lecturer/sections/"
            f"{OTHER_SECTION_ID}/gradebook"
        )

        self.assertEqual(
            response.headers.get("Cache-Control"),
            "no-store",
        )


if __name__ == "__main__":
    unittest.main()
