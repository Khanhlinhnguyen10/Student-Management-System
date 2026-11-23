
"""Unit tests for Create Account credential notification.

All SMTP calls are mocked.
No real email is sent.
No SQL Server connection is created.
"""

import smtplib
import ssl
import unittest
from unittest.mock import MagicMock

from app.services.create_account_notification_service import (
    AccountNotificationError,
    SMTPAccountNotifier,
)


STUDENT_ACCOUNT = {
    "accountType": "Student",
    "userId": "USR000000007",
    "username": "student_test01",
    "fullName": "Test Student",
    "studentId": "STU0000004",
    "lecturerId": None,
}

LECTURER_ACCOUNT = {
    "accountType": "Lecturer",
    "userId": "USR000000008",
    "username": "lecturer_test01",
    "fullName": "Test Lecturer",
    "studentId": None,
    "lecturerId": "LEC0000003",
}


class AccountNotificationTests(unittest.TestCase):

    def setUp(self):
        self.factory = MagicMock()

        self.smtp = (
            self.factory.return_value
            .__enter__.return_value
        )

        self.notifier = SMTPAccountNotifier(
            host="smtp.example.test",
            port=465,
            username="sender@example.test",
            password="mock-smtp-secret",
            sender="sender@example.test",
            smtp_factory=self.factory,
        )

        self.student_credentials = {
            "username": "student_test01",
            "initialPassword": "Example!Password123",
        }

    def test_send_student_credentials(self):
        result = self.notifier.deliver(
            account=STUDENT_ACCOUNT,
            credentials=self.student_credentials,
            email="student@example.test",
        )

        self.assertIsNone(result)

        self.factory.assert_called_once()

        self.assertIsInstance(
            self.factory.call_args.kwargs["context"],
            ssl.SSLContext,
        )

        self.smtp.login.assert_called_once_with(
            "sender@example.test",
            "mock-smtp-secret",
        )

        self.smtp.send_message.assert_called_once()

        message = (
            self.smtp.send_message
            .call_args.args[0]
        )

        self.assertEqual(
            message["To"],
            "student@example.test",
        )

        self.assertIn(
            "STU0000004",
            message.get_content(),
        )

        self.assertIn(
            "Example!Password123",
            message.get_content(),
        )

    def test_send_lecturer_credentials(self):
        self.notifier.deliver(
            account=LECTURER_ACCOUNT,
            credentials={
                "username": "lecturer_test01",
                "initialPassword": "Lecturer!Password123",
            },
            email="lecturer@example.test",
        )

        message = (
            self.smtp.send_message
            .call_args.args[0]
        )

        self.assertIn(
            "LEC0000003",
            message.get_content(),
        )

        self.assertIn(
            "Lecturer",
            message.get_content(),
        )

    def test_reject_missing_recipient(self):
        with self.assertRaises(ValueError):
            self.notifier.deliver(
                account=STUDENT_ACCOUNT,
                credentials=self.student_credentials,
                email=None,
            )

        self.factory.assert_not_called()

    def test_reject_username_mismatch(self):
        with self.assertRaises(ValueError):
            self.notifier.deliver(
                account=STUDENT_ACCOUNT,
                credentials={
                    "username": "another_username",
                    "initialPassword": "Example!Password123",
                },
                email="student@example.test",
            )

        self.factory.assert_not_called()

    def test_smtp_failure(self):
        self.smtp.send_message.side_effect = (
            smtplib.SMTPException(
                "Simulated SMTP failure"
            )
        )

        with self.assertRaises(
            AccountNotificationError
        ):
            self.notifier.deliver(
                account=STUDENT_ACCOUNT,
                credentials=self.student_credentials,
                email="student@example.test",
            )

    def test_invalid_smtp_configuration(self):
        with self.assertRaises(ValueError):
            SMTPAccountNotifier(
                host="",
                port=465,
                username="sender@example.test",
                password="mock-secret",
                sender="sender@example.test",
            )


if __name__ == "__main__":
    unittest.main()
