
"""Unit tests: database settings and connection setup, no live SQL required."""

import os
import unittest
from unittest.mock import patch

from app.repositories.database import (
    DatabaseConfigurationError,
    DatabaseSettings,
    get_connection,
)


class DatabaseConfigTestCase(unittest.TestCase):

    def setUp(self):
        self.base_env = {
            "DB_SERVER": r"localhost\SQLEXPRESS",
            "DB_DATABASE": "StudentManagementSystem",
            "DB_DRIVER": "ODBC Driver 18 for SQL Server",
            "DB_AUTH_MODE": "windows",
            "DB_ENCRYPT": "true",
            "DB_TRUST_SERVER_CERTIFICATE": "true",
            "DB_TIMEOUT": "5",
        }

    def test_windows_authentication_builds_string(self):
        with patch.dict(os.environ, self.base_env, clear=True):
            config = DatabaseSettings.from_environment()
            value = config.connection_string()

        self.assertIn("Trusted_Connection=yes", value)
        self.assertIn("Encrypt=yes", value)
        self.assertNotIn("PWD=", value)

    def test_sql_authentication_accepts_password_with_semicolon(self):
        env = self.base_env | {
            "DB_AUTH_MODE": "sql",
            "DB_USERNAME": "app_user",
            "DB_PASSWORD": "local;test;password",
        }

        with patch.dict(os.environ, env, clear=True):
            config = DatabaseSettings.from_environment()
            value = config.connection_string()

        self.assertIn("UID={app_user}", value)
        self.assertIn("PWD={local;test;password}", value)
        self.assertNotIn("Trusted_Connection=yes", value)
        self.assertNotIn("local;test;password", repr(config))

    def test_missing_server_is_rejected(self):
        env = {
            k: v for k, v in self.base_env.items()
            if k != "DB_SERVER"
        }

        with patch.dict(os.environ, env, clear=True):
            with self.assertRaisesRegex(
                DatabaseConfigurationError, "DB_SERVER"
            ):
                DatabaseSettings.from_environment()

    def test_missing_database_is_rejected(self):
        env = {
            k: v for k, v in self.base_env.items()
            if k != "DB_DATABASE"
        }

        with patch.dict(os.environ, env, clear=True):
            with self.assertRaisesRegex(
                DatabaseConfigurationError, "DB_DATABASE"
            ):
                DatabaseSettings.from_environment()

    def test_sql_authentication_requires_credentials(self):
        env = self.base_env | {
            "DB_AUTH_MODE": "sql",
        }

        with patch.dict(os.environ, env, clear=True):
            with self.assertRaisesRegex(
                DatabaseConfigurationError, "DB_USERNAME"
            ):
                DatabaseSettings.from_environment()

    def test_authentication_mode_is_checked(self):
        env = self.base_env | {
            "DB_AUTH_MODE": "unknown",
        }

        with patch.dict(os.environ, env, clear=True):
            with self.assertRaisesRegex(
                DatabaseConfigurationError, "DB_AUTH_MODE"
            ):
                DatabaseSettings.from_environment()

    def test_invalid_boolean_is_checked(self):
        env = self.base_env | {
            "DB_ENCRYPT": "perhaps",
        }

        with patch.dict(os.environ, env, clear=True):
            with self.assertRaisesRegex(
                DatabaseConfigurationError, "DB_ENCRYPT"
            ):
                DatabaseSettings.from_environment()

    def test_timeout_must_be_in_range(self):
        env = self.base_env | {
            "DB_TIMEOUT": "60",
        }

        with patch.dict(os.environ, env, clear=True):
            with self.assertRaisesRegex(
                DatabaseConfigurationError, "DB_TIMEOUT"
            ):
                DatabaseSettings.from_environment()

    @patch("app.repositories.database.pyodbc.connect")
    @patch("app.repositories.database.pyodbc.drivers")
    def test_get_connection_uses_configured_odbc_driver(
        self, drivers_mock, connect_mock
    ):
        drivers_mock.return_value = [
            "ODBC Driver 18 for SQL Server"
        ]

        with patch.dict(os.environ, self.base_env, clear=True):
            get_connection()

        self.assertEqual(connect_mock.call_count, 1)
        self.assertEqual(
            connect_mock.call_args.kwargs["timeout"], 5
        )
        self.assertFalse(
            connect_mock.call_args.kwargs["autocommit"]
        )


if __name__ == "__main__":
    unittest.main()
