
"""Unit tests for UserSession and GradeScale."""

import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.models.user_session import UserSession
from app.models.grade_scale import GradeScale


class UserSessionTests(unittest.TestCase):

    def make_session(self, expires_in_minutes=10):
        now = datetime.now(timezone.utc)

        return UserSession(
            sessionId="session-test-1",
            createdAt=now - timedelta(minutes=5),
            lastActivityAt=now - timedelta(minutes=1),
            expiresAt=now + timedelta(
                minutes=expires_in_minutes
            ),
            isActive=True,
        )

    def test_valid_session(self):
        session = self.make_session()

        self.assertFalse(session.isExpired())

    def test_refresh(self):
        session = self.make_session()

        session.refresh()

        self.assertFalse(session.isExpired())
        self.assertGreater(
            session.expiresAt,
            session.lastActivityAt
        )

    def test_terminate(self):
        session = self.make_session()

        session.terminate()

        self.assertTrue(session.isExpired())

        with self.assertRaises(ValueError):
            session.refresh()

    def test_expired_session_cannot_refresh(self):
        session = self.make_session(
            expires_in_minutes=-1
        )

        self.assertTrue(session.isExpired())

        with self.assertRaises(ValueError):
            session.refresh()


class GradeScaleTests(unittest.TestCase):

    def make_scale(self):
        # Test-only values, not the official grading policy.
        return GradeScale(
            letterGrade="TEST",
            minScore=Decimal("7.00"),
            maxScore=Decimal("8.00"),
            gradePoint=Decimal("3.00"),
        )

    def test_convert_within_configured_interval(self):
        scale = self.make_scale()

        result = scale.convert(
            Decimal("7.50")
        )

        self.assertEqual(result, "TEST")

    def test_convert_outside_interval_fails(self):
        scale = self.make_scale()

        with self.assertRaises(ValueError):
            scale.convert(Decimal("9.00"))

    def test_invalid_interval_fails(self):
        with self.assertRaises(ValueError):
            GradeScale(
                letterGrade="TEST",
                minScore=Decimal("8.00"),
                maxScore=Decimal("7.00"),
                gradePoint=Decimal("3.00"),
            )


if __name__ == "__main__":
    unittest.main()
