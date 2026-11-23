
"""Unit tests for transaction boundaries without a live SQL Server."""

import unittest
from unittest.mock import Mock

from app.repositories.transaction import connection_scope


class TransactionScopeTests(unittest.TestCase):

    def setUp(self):
        self.conn = Mock()
        self.factory = Mock(return_value=self.conn)

    def test_read_scope_rolls_back_on_success(self):
        with connection_scope(
            connection_factory=self.factory
        ) as conn:
            self.assertIs(conn, self.conn)

        self.conn.rollback.assert_called_once_with()
        self.conn.commit.assert_not_called()
        self.conn.close.assert_called_once_with()

    def test_write_scope_commits_on_success(self):
        with connection_scope(
            write=True,
            connection_factory=self.factory,
        ):
            pass

        self.conn.commit.assert_called_once_with()
        self.conn.rollback.assert_not_called()
        self.conn.close.assert_called_once_with()

    def test_write_scope_rolls_back_on_application_error(self):
        with self.assertRaisesRegex(RuntimeError, "failed"):
            with connection_scope(
                write=True,
                connection_factory=self.factory,
            ):
                raise RuntimeError("failed")

        self.conn.commit.assert_not_called()
        self.conn.rollback.assert_called_once_with()
        self.conn.close.assert_called_once_with()

    def test_read_scope_rolls_back_on_error(self):
        with self.assertRaises(ValueError):
            with connection_scope(
                connection_factory=self.factory
            ):
                raise ValueError("query failed")

        self.conn.rollback.assert_called_once_with()
        self.conn.close.assert_called_once_with()

    def test_failed_commit_triggers_rollback(self):
        self.conn.commit.side_effect = RuntimeError(
            "commit failed"
        )

        with self.assertRaisesRegex(
            RuntimeError, "commit failed"
        ):
            with connection_scope(
                write=True,
                connection_factory=self.factory,
            ):
                pass

        self.conn.rollback.assert_called_once_with()
        self.conn.close.assert_called_once_with()

    def test_factory_failure_is_not_hidden(self):
        self.factory.side_effect = RuntimeError(
            "cannot connect"
        )

        with self.assertRaisesRegex(
            RuntimeError, "cannot connect"
        ):
            with connection_scope(
                connection_factory=self.factory
            ):
                pass

    def test_write_parameter_must_be_bool(self):
        with self.assertRaises(ValueError):
            with connection_scope(
                write="yes",
                connection_factory=self.factory,
            ):
                pass

        self.factory.assert_not_called()


if __name__ == "__main__":
    unittest.main()
