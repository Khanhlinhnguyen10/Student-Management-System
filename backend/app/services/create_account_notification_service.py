
"""Credential notification for Group 05 Create Account.

Implements the notification step of Use Case 11.

Uses SMTP over verified TLS.
Does not change the database or create business entities.
"""

from email.message import EmailMessage
import re
import smtplib
import ssl
from typing import Any, Callable


class AccountNotificationError(RuntimeError):
    """Credential delivery failed."""


class SMTPAccountNotifier:
    """Send initial account credentials by email."""

    def __init__(
        self,
        *,
        host: str,
        port: int,
        username: str,
        password: str,
        sender: str,
        smtp_factory: Callable[..., Any] | None = None,
    ):
        if not isinstance(host, str) or not host.strip():
            raise ValueError("SMTP host is required.")

        if type(port) is not int or not 1 <= port <= 65535:
            raise ValueError("Invalid SMTP port.")

        if not isinstance(username, str) or not username.strip():
            raise ValueError("SMTP username is required.")

        if not isinstance(password, str) or not password:
            raise ValueError("SMTP password is required.")

        if not self._valid_email(sender):
            raise ValueError("Invalid SMTP sender address.")

        self._host = host.strip()
        self._port = port
        self._username = username.strip()
        self._password = password
        self._sender = sender.strip()
        self._smtp_factory = smtp_factory or smtplib.SMTP_SSL

    @staticmethod
    def _valid_email(value) -> bool:
        if not isinstance(value, str):
            return False

        value = value.strip()

        return bool(
            re.fullmatch(
                r"[^@\s]+@[^@\s]+\.[^@\s]+",
                value,
            )
        )

    def deliver(
        self,
        *,
        account: dict,
        credentials: dict,
        email: str | None,
        phone_number: str | None = None,
    ) -> None:
        """Deliver credentials after account creation commits.

        phone_number belongs to the controller interface,
        but this implementation uses the registered email.
        """

        if not isinstance(account, dict):
            raise ValueError("Invalid account data.")

        if not isinstance(credentials, dict):
            raise ValueError("Invalid credential data.")

        if not self._valid_email(email):
            raise ValueError("Valid recipient email is required.")

        account_type = account.get("accountType")

        if account_type not in ("Student", "Lecturer"):
            raise ValueError("Invalid account type.")

        username = credentials.get("username")
        initial_password = credentials.get("initialPassword")

        if (
            not isinstance(username, str)
            or not username
            or username != account.get("username")
        ):
            raise ValueError("Account username does not match.")

        if (
            not isinstance(initial_password, str)
            or not initial_password
        ):
            raise ValueError("Initial password is required.")

        if account_type == "Student":
            account_id = account.get("studentId")
            id_label = "Student ID"
        else:
            account_id = account.get("lecturerId")
            id_label = "Lecturer ID"

        if not isinstance(account_id, str) or not account_id:
            raise ValueError("Account identifier is required.")

        recipient = email.strip()

        message = EmailMessage()

        message["Subject"] = (
            "Student Management System - Account Information"
        )
        message["From"] = self._sender
        message["To"] = recipient

        message.set_content(
            "Student Management System - Group 05\n\n"
            "Your account has been created.\n\n"
            f"Account type: {account_type}\n"
            f"{id_label}: {account_id}\n"
            f"Username: {username}\n"
            f"Initial password: {initial_password}\n\n"
            "Keep your credentials private.\n"
            "You can change your password after signing in.\n"
        )

        try:
            # SMTP over TLS, normally port 465.
            # Certificate verification is enabled.
            tls_context = ssl.create_default_context()

            with self._smtp_factory(
                self._host,
                self._port,
                timeout=8,
                context=tls_context,
            ) as smtp:
                smtp.login(
                    self._username,
                    self._password,
                )

                smtp.send_message(message)

        except (smtplib.SMTPException, OSError) as exc:
            # Never include credentials in the exception.
            raise AccountNotificationError(
                "Unable to deliver account credentials."
            ) from exc
