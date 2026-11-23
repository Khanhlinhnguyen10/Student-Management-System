
"""Tests for Change Password - Group 05."""

import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from werkzeug.security import (
    check_password_hash,
    generate_password_hash,
)

from app import create_app

from app.controllers.auth_security import (
    SESSION_COOKIE_NAME,
    csrf_token_for_session,
)

from app.services.change_password_service import (
    ChangePasswordService,
    IncorrectCurrentPasswordError,
    PasswordChangeError,
    PasswordUpdateConflictError,
)


USER_ID = "USR000000002"
TOKEN = "t" * 43

CURRENT_PASSWORD = "Current#123"
NEW_PASSWORD = "NewSecure#456"


# =============================================
# SERVICE TESTS
# =============================================

class ChangePasswordServiceTests(unittest.TestCase):

    def setUp(self):
        self.repository = Mock()

        self.old_hash = generate_password_hash(
            CURRENT_PASSWORD,
            method="pbkdf2:sha256:1000",
        )

        self.repository.get_password_hash.return_value = (
            self.old_hash
        )

        self.repository.replace_password_hash_if_unchanged.return_value = (
            True
        )

        self.service = ChangePasswordService(
            self.repository
        )

    def change(self, current=CURRENT_PASSWORD,
               new=NEW_PASSWORD, confirm=NEW_PASSWORD):
        return self.service.change_password(
            user_id=USER_ID,
            current_password=current,
            new_password=new,
            confirm_password=confirm,
        )

    def test_successful_password_change(self):
        result = self.change()

        self.assertIn("successfully", result["message"])

        kwargs = (
            self.repository
            .replace_password_hash_if_unchanged
            .call_args.kwargs
        )

        self.assertEqual(kwargs["user_id"], USER_ID)
        self.assertEqual(kwargs["old_hash"], self.old_hash)

        self.assertTrue(
            check_password_hash(
                kwargs["new_hash"],
                NEW_PASSWORD,
            )
        )

    def test_wrong_current_password(self):
        with self.assertRaises(
            IncorrectCurrentPasswordError
        ):
            self.change(current="Wrong#123")

        self.repository.replace_password_hash_if_unchanged.assert_not_called()

    def test_confirmation_mismatch(self):
        with self.assertRaises(PasswordChangeError):
            self.change(confirm="Different#123")

        self.repository.replace_password_hash_if_unchanged.assert_not_called()

    def test_weak_new_password(self):
        with self.assertRaises(PasswordChangeError):
            self.change(new="weak", confirm="weak")

        self.repository.replace_password_hash_if_unchanged.assert_not_called()

    def test_cannot_reuse_current_password(self):
        with self.assertRaises(PasswordChangeError):
            self.change(
                new=CURRENT_PASSWORD,
                confirm=CURRENT_PASSWORD,
            )

        self.repository.replace_password_hash_if_unchanged.assert_not_called()

    def test_concurrent_password_update(self):
        self.repository.replace_password_hash_if_unchanged.return_value = (
            False
        )

        with self.assertRaises(
            PasswordUpdateConflictError
        ):
            self.change()


# =============================================
# CONTROLLER / API TESTS
# =============================================

class ChangePasswordApiTests(unittest.TestCase):

    def setUp(self):
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "change-password-test-secret",
            "AUTH_ALLOWED_ORIGIN": "http://localhost:5173",
        })

        self.auth = Mock()

        self.auth.current_user.return_value = SimpleNamespace(
            user_id=USER_ID,
            role="Student",
        )

        self.app.extensions["sms_auth_service"] = self.auth

        self.service = Mock()

        self.service.change_password.return_value = {
            "message": "Password changed successfully."
        }

        self.app.extensions[
            "sms_change_password_service"
        ] = self.service

        self.client = self.app.test_client()

        with self.app.app_context():
            self.csrf = csrf_token_for_session(TOKEN)

        self.payload = {
            "currentPassword": CURRENT_PASSWORD,
            "newPassword": NEW_PASSWORD,
            "confirmPassword": NEW_PASSWORD,
        }

    def login(self):
        self.client.set_cookie(
            SESSION_COOKIE_NAME,
            TOKEN,
            path="/api",
        )

    def post(self):
        return self.client.post(
            "/api/auth/change-password",
            json=self.payload,
            headers={
                "Origin": "http://localhost:5173",
                "X-CSRF-Token": self.csrf,
            },
        )

    def test_guest_gets_401(self):
        response = self.post()

        self.assertEqual(response.status_code, 401)
        self.service.change_password.assert_not_called()

    def test_student_can_change_password(self):
        self.login()

        response = self.post()

        self.assertEqual(response.status_code, 200)

        self.service.change_password.assert_called_once_with(
            user_id=USER_ID,
            current_password=CURRENT_PASSWORD,
            new_password=NEW_PASSWORD,
            confirm_password=NEW_PASSWORD,
        )

    def test_lecturer_can_change_password(self):
        self.login()
        self.auth.current_user.return_value.role = "Lecturer"

        response = self.post()

        self.assertEqual(response.status_code, 200)

    def test_administrator_gets_403(self):
        self.login()
        self.auth.current_user.return_value.role = "Administrator"

        response = self.post()

        self.assertEqual(response.status_code, 403)
        self.service.change_password.assert_not_called()

    def test_missing_csrf_gets_403(self):
        self.login()

        response = self.client.post(
            "/api/auth/change-password",
            json=self.payload,
            headers={
                "Origin": "http://localhost:5173",
            },
        )

        self.assertEqual(response.status_code, 403)

    def test_unapproved_origin_gets_403(self):
        self.login()

        response = self.client.post(
            "/api/auth/change-password",
            json=self.payload,
            headers={
                "Origin": "https://example.com",
                "X-CSRF-Token": self.csrf,
            },
        )

        self.assertEqual(response.status_code, 403)

    def test_wrong_current_password_gets_400(self):
        self.login()

        self.service.change_password.side_effect = (
            IncorrectCurrentPasswordError()
        )

        response = self.post()

        self.assertEqual(response.status_code, 400)

    def test_concurrent_update_gets_409(self):
        self.login()

        self.service.change_password.side_effect = (
            PasswordUpdateConflictError()
        )

        response = self.post()

        self.assertEqual(response.status_code, 409)

    def test_database_error_gets_503(self):
        self.login()

        self.service.change_password.side_effect = (
            RuntimeError("PRIVATE_DATABASE_ERROR")
        )

        response = self.post()

        self.assertEqual(response.status_code, 503)

        self.assertNotIn(
            "PRIVATE_DATABASE_ERROR",
            str(response.json),
        )

    def test_response_is_not_cached(self):
        self.login()

        response = self.post()

        self.assertEqual(
            response.headers.get("Cache-Control"),
            "no-store",
        )


if __name__ == "__main__":
    unittest.main()
