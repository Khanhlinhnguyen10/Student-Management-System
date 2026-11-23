
"""AuthRepository unit tests using mocked pyodbc connections (no SQL writes)."""

from datetime import datetime, timezone
import unittest
from unittest.mock import Mock

from app.repositories.auth_repository import AuthRepository


class AuthRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.cursor = Mock()
        self.conn = Mock()
        self.conn.cursor.return_value = self.cursor
        self.factory = Mock(return_value=self.conn)
        self.repo = AuthRepository(connection_factory=self.factory)

    def test_get_username_joins_all_three_role_tables(self):
        self.cursor.fetchone.return_value = (
            "USR000000002", "student01", "hash", 0, "Tran Minh Anh", 0, 1, 0
        )
        account = self.repo.get_by_username("student01")
        self.assertEqual(account.roles, ("Student",))
        self.assertEqual(account.full_name, "Tran Minh Anh")
        sql, username = self.cursor.execute.call_args.args
        self.assertIn("dbo.Users", sql)
        for table in ("dbo.Administrators", "dbo.Students", "dbo.Lecturers"):
            self.assertIn(table, sql)
        self.assertIn("WHERE u.username = ?", sql)
        self.assertEqual(username, "student01")
        self.assertNotIn("student01", sql)
        self.conn.rollback.assert_called_once()
        self.conn.commit.assert_not_called()
        self.cursor.close.assert_called_once()
        self.conn.close.assert_called_once()

    def test_get_by_id_uses_parameter(self):
        self.cursor.fetchone.return_value = (
            "USR000000001", "admin01", "hash", 0, "Example", 1, 0, 0
        )
        account = self.repo.get_by_user_id("USR000000001")
        self.assertEqual(account.roles, ("Administrator",))
        sql, user_id = self.cursor.execute.call_args.args
        self.assertIn("WHERE u.userId = ?", sql)
        self.assertEqual(user_id, "USR000000001")

    def test_multiple_roles_are_detected_not_hidden(self):
        self.cursor.fetchone.return_value = (
            "USR000000001", "multi", "hash", 0, "Example", 1, 1, 0
        )
        result = self.repo.get_by_username("multi")
        self.assertEqual(result.roles, ("Administrator", "Student"))

    def test_locked_flag_and_sensitive_repr(self):
        self.cursor.fetchone.return_value = (
            "USR000000005", "lecturer01", "DO_NOT_SHOW_HASH", 1,
            "Example", 0, 0, 1
        )
        result = self.repo.get_by_username("lecturer01")
        self.assertTrue(result.is_locked)
        self.assertEqual(result.roles, ("Lecturer",))
        self.assertNotIn("DO_NOT_SHOW_HASH", repr(result))

    def test_missing_user_returns_none(self):
        self.cursor.fetchone.return_value = None
        self.assertIsNone(self.repo.get_by_username("unknown"))

    def test_invalid_username_without_connection(self):
        for username in ("", "x" * 51, 1, None):
            with self.subTest(username=username):
                with self.assertRaises(ValueError):
                    self.repo.get_by_username(username)
        self.factory.assert_not_called()

    def test_create_session_uses_only_hash_and_commits(self):
        expiration = datetime(2026, 11, 15, 8, 15)
        self.cursor.fetchone.return_value = (
            "00000000-0000-0000-0000-000000000001", "USR000000002", expiration
        )
        hashed = "a" * 64
        result = self.repo.create_session("USR000000002", hashed)
        self.assertEqual(result.user_id, "USR000000002")
        self.assertEqual(result.expires_at.tzinfo, timezone.utc)
        sql, user_id, token_hash = self.cursor.execute.call_args.args
        self.assertIn("dbo.usp_CreateUserSession", sql)
        self.assertEqual(user_id, "USR000000002")
        self.assertEqual(token_hash, hashed)
        self.conn.commit.assert_called_once()
        self.conn.close.assert_called_once()

    def test_create_session_mismatched_return_rolls_back(self):
        self.cursor.fetchone.return_value = (
            "some-session-id", "WRONG_USER", datetime(2026, 11, 15)
        )
        with self.assertRaises(RuntimeError):
            self.repo.create_session("USR000000002", "b" * 64)
        self.conn.commit.assert_not_called()
        self.conn.rollback.assert_called_once()
        self.conn.close.assert_called_once()

    def test_touch_expired_session_returns_none(self):
        self.cursor.fetchone.return_value = None
        self.assertIsNone(self.repo.touch_session("b" * 64))
        self.assertIn("dbo.usp_TouchUserSession", self.cursor.execute.call_args.args[0])
        self.conn.commit.assert_called_once()

    def test_touch_active_session_returns_utc(self):
        self.cursor.fetchone.return_value = (
            "USR000000002", datetime(2026, 11, 15, 8, 15)
        )
        result = self.repo.touch_session("b" * 64)
        self.assertEqual(result.user_id, "USR000000002")
        self.assertEqual(result.expires_at.tzinfo, timezone.utc)

    def test_revoke_session_confirmation(self):
        self.cursor.fetchone.return_value = (1,)
        self.assertTrue(self.repo.revoke_session("c" * 64))
        self.assertIn("dbo.usp_RevokeUserSession", self.cursor.execute.call_args.args[0])
        self.conn.commit.assert_called_once()

    def test_revoke_missing_session_returns_false(self):
        self.cursor.fetchone.return_value = (0,)
        self.assertFalse(self.repo.revoke_session("c" * 64))
        self.conn.commit.assert_called_once()

    def test_unexpected_revoke_count_rolls_back(self):
        self.cursor.fetchone.return_value = (2,)
        with self.assertRaises(RuntimeError):
            self.repo.revoke_session("c" * 64)
        self.conn.rollback.assert_called_once()
        self.conn.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
