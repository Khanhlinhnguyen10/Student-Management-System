
"""Unit tests for Group 05 Authentication HTTP endpoints.

These tests use a mocked AuthService and do not change SQL Server data.
"""

from datetime import datetime, timezone
from unittest.mock import Mock
import unittest

from flask import jsonify

from app import create_app
from app.controllers.auth_security import (
    SESSION_COOKIE_NAME,
    roles_required,
)
from app.services.auth_service import (
    AuthPrincipal,
    AuthenticationError,
    LoginResult,
    SessionExpiredError,
)


_ORIGIN = "http://localhost:5173"
_TOKEN = "a" * 43
_EXPIRY = datetime(
    2026, 11, 15, 10, 15, tzinfo=timezone.utc
)


class AuthApiTests(unittest.TestCase):

    def setUp(self):
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "unit-testing-only-secret-keep-private",
            "AUTH_ALLOWED_ORIGIN": _ORIGIN,
            "AUTH_COOKIE_SECURE": False,
            "AUTH_LOGIN_MAX_ATTEMPTS": 10,
            "AUTH_LOGIN_WINDOW_SECONDS": 60,
        })

        self.auth = Mock()
        self.app.extensions["sms_auth_service"] = self.auth

        self.auth.login.return_value = LoginResult(
            token=_TOKEN,
            user_id="USR000000002",
            username="student01",
            full_name="Tran Minh Anh",
            role="Student",
            expires_at=_EXPIRY,
        )

        self.auth.current_user.return_value = AuthPrincipal(
            user_id="USR000000002",
            username="student01",
            full_name="Tran Minh Anh",
            role="Student",
            expires_at=_EXPIRY,
        )

        self.auth.logout.return_value = True

        @self.app.get("/api/_test/admin-only")
        @roles_required("Administrator")
        def admin_only():
            return jsonify(ok=True)

        self.client = self.app.test_client()

    def _login(self, **overrides):
        data = {
            "username": "student01",
            "password": "CorrectPassword",
            "role": "student",
        }

        data.update(overrides)

        return self.client.post(
            "/api/auth/login",
            json=data,
            headers={"Origin": _ORIGIN},
        )

    def test_login_returns_public_user_and_secure_cookie_attributes(self):
        response = self._login()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json["user"]["role"],
            "Student",
        )
        self.assertEqual(
            response.json["user"]["fullName"],
            "Tran Minh Anh",
        )
        self.assertNotIn("token", response.json)

        cookie = response.headers["Set-Cookie"]

        self.assertIn("sms_auth=", cookie)
        self.assertIn("HttpOnly", cookie)
        self.assertIn("SameSite=Lax", cookie)
        self.assertIn("Path=/api", cookie)
        self.assertNotIn("Max-Age", cookie)

        self.assertEqual(
            response.headers["Cache-Control"],
            "no-store",
        )

    def test_login_does_not_accept_cross_origin(self):
        response = self.client.post(
            "/api/auth/login",
            json={
                "username": "student01",
                "password": "x",
                "role": "student",
            },
            headers={
                "Origin": "https://attacker.invalid"
            },
        )

        self.assertEqual(response.status_code, 403)
        self.auth.login.assert_not_called()

    def test_login_rejects_lookalike_origin(self):
        response = self.client.post(
            "/api/auth/login",
            json={
                "username": "student01",
                "password": "x",
                "role": "student",
            },
            headers={
                "Origin": "http://localhost:5173.attacker.invalid"
            },
        )

        self.assertEqual(response.status_code, 403)
        self.auth.login.assert_not_called()

    def test_login_rejects_malformed_origin(self):
        response = self.client.post(
            "/api/auth/login",
            json={
                "username": "student01",
                "password": "x",
                "role": "student",
            },
            headers={"Origin": "http://[invalid"},
        )

        self.assertEqual(response.status_code, 403)
        self.auth.login.assert_not_called()

    def test_login_rejects_missing_origin_or_referer(self):
        response = self.client.post(
            "/api/auth/login",
            json={
                "username": "student01",
                "password": "x",
                "role": "student",
            },
        )

        self.assertEqual(response.status_code, 403)
        self.auth.login.assert_not_called()

    def test_login_accepts_approved_referer_fallback(self):
        response = self.client.post(
            "/api/auth/login",
            json={
                "username": "student01",
                "password": "x",
                "role": "student",
            },
            headers={
                "Referer": _ORIGIN + "/login"
            },
        )

        self.assertEqual(response.status_code, 200)

    def test_login_requires_json(self):
        response = self.client.post(
            "/api/auth/login",
            data="username=student01",
            headers={"Origin": _ORIGIN},
        )

        self.assertEqual(response.status_code, 415)
        self.auth.login.assert_not_called()

    def test_login_rejects_invalid_json_shape(self):
        response = self.client.post(
            "/api/auth/login",
            json=["not", "object"],
            headers={"Origin": _ORIGIN},
        )

        self.assertEqual(response.status_code, 400)
        self.auth.login.assert_not_called()

    def test_login_wrong_credentials_no_cookie(self):
        self.auth.login.side_effect = AuthenticationError(
            "generic"
        )

        response = self._login(password="incorrect")

        self.assertEqual(response.status_code, 401)
        self.assertNotIn(
            "Set-Cookie",
            response.headers,
        )
        self.assertNotIn(
            "student01",
            str(response.json),
        )

    def test_login_sql_error_is_sanitized(self):
        self.auth.login.side_effect = RuntimeError(
            "PRIVATE_DB_ERROR"
        )

        response = self._login()

        self.assertEqual(response.status_code, 503)
        self.assertNotIn(
            "PRIVATE_DB_ERROR",
            str(response.json),
        )

    def test_login_rate_limit_rejects_excess_attempts(self):
        self.app.extensions[
            "sms_login_limiter"
        ].limit = 2

        self.assertEqual(
            self._login().status_code, 200
        )
        self.assertEqual(
            self._login().status_code, 200
        )

        third = self._login()

        self.assertEqual(third.status_code, 429)
        self.assertIn(
            "Retry-After",
            third.headers,
        )
        self.assertEqual(
            self.auth.login.call_count, 2
        )

    def test_me_requires_cookie(self):
        response = self.client.get(
            "/api/auth/me"
        )

        self.assertEqual(response.status_code, 401)
        self.auth.current_user.assert_not_called()

    def test_me_reads_user_from_sql_backed_service(self):
        self._login()

        response = self.client.get(
            "/api/auth/me"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json["user"]["role"],
            "Student",
        )
        self.assertNotIn("token", response.json)

        self.auth.current_user.assert_called_once_with(
            _TOKEN
        )

    def test_me_expired_session_clears_browser_cookie(self):
        self._login()

        self.auth.current_user.side_effect = (
            SessionExpiredError("expired")
        )

        response = self.client.get(
            "/api/auth/me"
        )

        self.assertEqual(response.status_code, 401)
        self.assertIn(
            "Max-Age=0",
            response.headers["Set-Cookie"],
        )

    def test_me_service_unavailable_is_sanitized(self):
        self._login()

        self.auth.current_user.side_effect = RuntimeError(
            "SQL_PRIVATE"
        )

        response = self.client.get(
            "/api/auth/me"
        )

        self.assertEqual(response.status_code, 503)
        self.assertNotIn(
            "SQL_PRIVATE",
            str(response.json),
        )

    def test_admin_guard_blocks_student_role(self):
        self._login()

        response = self.client.get(
            "/api/_test/admin-only"
        )

        self.assertEqual(response.status_code, 403)

    def test_admin_guard_allows_administrator_role(self):
        self._login()

        self.auth.current_user.return_value = AuthPrincipal(
            user_id="USR000000001",
            username="admin01",
            full_name="Admin",
            role="Administrator",
            expires_at=_EXPIRY,
        )

        response = self.client.get(
            "/api/_test/admin-only"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json,
            {"ok": True},
        )

    def test_csrf_requires_authenticated_session(self):
        response = self.client.get(
            "/api/auth/csrf"
        )

        self.assertEqual(response.status_code, 401)

    def test_csrf_is_not_raw_session_token(self):
        self._login()

        response = self.client.get(
            "/api/auth/csrf"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            len(response.json["csrfToken"]), 64
        )
        self.assertNotEqual(
            response.json["csrfToken"],
            _TOKEN,
        )
        self.assertEqual(
            response.headers["Cache-Control"],
            "no-store",
        )

    def test_logout_rejects_missing_csrf_token(self):
        self._login()

        response = self.client.post(
            "/api/auth/logout",
            headers={"Origin": _ORIGIN},
        )

        self.assertEqual(response.status_code, 403)
        self.auth.logout.assert_not_called()

    def test_logout_rejects_forged_csrf_token(self):
        self._login()

        response = self.client.post(
            "/api/auth/logout",
            headers={
                "Origin": _ORIGIN,
                "X-CSRF-Token": "0" * 64,
            },
        )

        self.assertEqual(response.status_code, 403)
        self.auth.logout.assert_not_called()

    def test_logout_rejects_cross_origin(self):
        self._login()

        csrf = self.client.get(
            "/api/auth/csrf"
        ).json["csrfToken"]

        response = self.client.post(
            "/api/auth/logout",
            headers={
                "Origin": "https://attacker.invalid",
                "X-CSRF-Token": csrf,
            },
        )

        self.assertEqual(response.status_code, 403)
        self.auth.logout.assert_not_called()

    def test_logout_with_valid_csrf_revokes_and_deletes_cookie(self):
        self._login()

        csrf = self.client.get(
            "/api/auth/csrf"
        ).json["csrfToken"]

        response = self.client.post(
            "/api/auth/logout",
            headers={
                "Origin": _ORIGIN,
                "X-CSRF-Token": csrf,
            },
        )

        self.assertEqual(response.status_code, 200)

        self.auth.logout.assert_called_once_with(
            _TOKEN
        )

        self.assertIn(
            "Max-Age=0",
            response.headers["Set-Cookie"],
        )

    def test_logout_unconfirmed_does_not_clear_cookie(self):
        self._login()

        csrf = self.client.get(
            "/api/auth/csrf"
        ).json["csrfToken"]

        self.auth.logout.return_value = False

        response = self.client.post(
            "/api/auth/logout",
            headers={
                "Origin": _ORIGIN,
                "X-CSRF-Token": csrf,
            },
        )

        self.assertEqual(response.status_code, 401)
        self.assertNotIn(
            "Set-Cookie",
            response.headers,
        )

    def test_logout_sql_error_does_not_clear_cookie(self):
        self._login()

        csrf = self.client.get(
            "/api/auth/csrf"
        ).json["csrfToken"]

        self.auth.logout.side_effect = RuntimeError(
            "db failure"
        )

        response = self.client.post(
            "/api/auth/logout",
            headers={
                "Origin": _ORIGIN,
                "X-CSRF-Token": csrf,
            },
        )

        self.assertEqual(response.status_code, 503)
        self.assertNotIn(
            "Set-Cookie",
            response.headers,
        )

    def test_login_cookie_can_be_secure_in_production(self):
        self.app.config[
            "AUTH_COOKIE_SECURE"
        ] = True

        response = self._login()

        self.assertIn(
            "Secure",
            response.headers["Set-Cookie"],
        )


if __name__ == "__main__":
    unittest.main()
