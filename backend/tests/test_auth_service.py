
"""AuthService unit tests for credentials, role matching, token/session and RBAC.

All database interactions are mocked. These tests do not make new sessions.
"""

from datetime import datetime, timezone
import hashlib
import unittest
from unittest.mock import Mock, patch

from werkzeug.security import generate_password_hash

from app.repositories.auth_repository import AuthAccount, StoredSession
from app.services.auth_service import (
    AccessDeniedError,
    AuthService,
    AuthenticationError,
    SessionExpiredError,
)


class AuthServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.password = "CorrectTestPassword!2026"
        # A deliberately inexpensive hash for fast unit tests only.
        cls.password_hash = generate_password_hash(
            cls.password, method="pbkdf2:sha256:1000"
        )

    def setUp(self):
        self.repo = Mock()
        self.service = AuthService(repository=self.repo)
        self.account = AuthAccount(
            user_id="USR000000002",
            username="student01",
            password_hash=self.password_hash,
            is_locked=False,
            full_name="Tran Minh Anh",
            roles=("Student",),
        )
        self.expiry = datetime(2026, 11, 15, 10, 15, tzinfo=timezone.utc)
        self.repo.get_by_username.return_value = self.account
        self.repo.get_by_user_id.return_value = self.account
        self.repo.create_session.return_value = StoredSession(
            user_id=self.account.user_id, expires_at=self.expiry
        )
        self.repo.touch_session.return_value = StoredSession(
            user_id=self.account.user_id, expires_at=self.expiry
        )

    def test_successful_student_login(self):
        result = self.service.login("student01", self.password, "student")
        self.assertEqual(result.role, "Student")
        self.assertEqual(result.user_id, "USR000000002")
        self.assertEqual(result.full_name, "Tran Minh Anh")
        self.assertEqual(len(result.token), 43)
        self.repo.create_session.assert_called_once()
        self.assertNotIn(result.token, repr(result))

    def test_raw_token_not_sent_to_sql(self):
        result = self.service.login("student01", self.password, "Student")
        args = self.repo.create_session.call_args.args
        self.assertEqual(args[0], "USR000000002")
        self.assertEqual(args[1], hashlib.sha256(result.token.encode()).hexdigest())
        self.assertNotEqual(args[1], result.token)
        self.assertEqual(len(args[1]), 64)

    def test_wrong_password_creates_no_session(self):
        with self.assertRaises(AuthenticationError):
            self.service.login("student01", "WRONG", "student")
        self.repo.create_session.assert_not_called()

    def test_wrong_role_creates_no_session_and_same_error(self):
        errors = []
        for role, password in (("admin", self.password), ("student", "WRONG")):
            with self.assertRaises(AuthenticationError) as context:
                self.service.login("student01", password, role)
            errors.append(str(context.exception))
        self.assertEqual(errors[0], errors[1])
        self.repo.create_session.assert_not_called()

    def test_locked_account_creates_no_session(self):
        self.repo.get_by_username.return_value = AuthAccount(
            user_id=self.account.user_id,
            username="student01",
            password_hash=self.password_hash,
            is_locked=True,
            roles=("Student",),
        )
        with self.assertRaises(AuthenticationError):
            self.service.login("student01", self.password, "student")
        self.repo.create_session.assert_not_called()

    def test_unknown_user_creates_no_session(self):
        self.repo.get_by_username.return_value = None
        with self.assertRaises(AuthenticationError):
            self.service.login("missing", self.password, "student")
        self.repo.create_session.assert_not_called()

    def test_ambiguous_roles_are_denied(self):
        self.repo.get_by_username.return_value = AuthAccount(
            user_id=self.account.user_id, username="student01",
            password_hash=self.password_hash,
            roles=("Administrator", "Student"),
        )
        with self.assertRaises(AuthenticationError):
            self.service.login("student01", self.password, "student")
        self.repo.create_session.assert_not_called()

    def test_invalid_login_input_does_not_query_sql(self):
        invalid = (
            ("", self.password, "student"),
            ("student01", "", "student"),
            ("student01", self.password, "teacher"),
            (None, self.password, "student"),
        )
        for username, password, role in invalid:
            with self.subTest(username=username, role=role):
                with self.assertRaises(AuthenticationError):
                    self.service.login(username, password, role)
        self.repo.get_by_username.assert_not_called()

    def test_admin_alias_is_supported(self):
        self.repo.get_by_username.return_value = AuthAccount(
            user_id="USR000000001", username="admin01",
            password_hash=self.password_hash, roles=("Administrator",),
        )
        self.repo.create_session.return_value = StoredSession(
            user_id="USR000000001", expires_at=self.expiry
        )
        result = self.service.login("admin01", self.password, "admin")
        self.assertEqual(result.role, "Administrator")

    def test_current_user_renews_session(self):
        with patch("app.services.auth_service.secrets.token_urlsafe", return_value="x" * 43):
            token = self.service.login("student01", self.password, "student").token
        current = self.service.current_user(token)
        self.assertEqual(current.role, "Student")
        expected = hashlib.sha256(token.encode()).hexdigest()
        self.repo.touch_session.assert_called_once_with(expected)
        self.assertEqual(current.expires_at, self.expiry)

    def test_expired_session_rejected(self):
        self.repo.touch_session.return_value = None
        with self.assertRaises(SessionExpiredError):
            self.service.current_user("x" * 43)
        self.repo.get_by_user_id.assert_not_called()

    def test_malformed_token_cannot_reach_db(self):
        for token in ("", "not-a-token", "a" * 300, None):
            with self.subTest(token=token):
                with self.assertRaises(SessionExpiredError):
                    self.service.current_user(token)
        self.repo.touch_session.assert_not_called()

    def test_role_changed_to_multiple_revokes_session(self):
        self.repo.get_by_user_id.return_value = AuthAccount(
            user_id=self.account.user_id, username="student01",
            password_hash=self.password_hash,
            roles=("Student", "Administrator"),
        )
        with self.assertRaises(SessionExpiredError):
            self.service.current_user("x" * 43)
        self.repo.revoke_session.assert_called_once()

    def test_backend_role_guard_denies_student_admin_action(self):
        with self.assertRaises(AccessDeniedError):
            self.service.require_role("x" * 43, "admin")
        self.repo.touch_session.assert_called_once()

    def test_backend_role_guard_allows_student_action(self):
        principal = self.service.require_role("x" * 43, "student")
        self.assertEqual(principal.user_id, "USR000000002")

    def test_logout_calls_database_and_checks_result(self):
        self.repo.revoke_session.return_value = True
        self.assertTrue(self.service.logout("x" * 43))
        digest = hashlib.sha256(("x" * 43).encode()).hexdigest()
        self.repo.revoke_session.assert_called_once_with(digest)

    def test_logout_unconfirmed_is_not_success(self):
        self.repo.revoke_session.return_value = False
        self.assertFalse(self.service.logout("x" * 43))

    def test_unknown_required_role_is_programmer_error(self):
        with self.assertRaises(ValueError):
            self.service.require_role("x" * 43, "teacher")
        self.repo.touch_session.assert_not_called()


if __name__ == "__main__":
    unittest.main()
