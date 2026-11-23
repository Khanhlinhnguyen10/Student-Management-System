
"""Tests for course faculty data in Assign Lecturer.

These tests use mocks and never modify SQL Server.
"""

import unittest
from datetime import time
from unittest.mock import MagicMock

from app.repositories.assign_lecturer_repository import (
    AssignLecturerRepository,
)


class AssignLecturerFacultyDataTests(unittest.TestCase):

    def setUp(self):
        self.connection = MagicMock()
        self.cursor = self.connection.cursor.return_value

        self.factory = MagicMock(
            return_value=self.connection
        )

        self.repo = AssignLecturerRepository(
            connection_factory=self.factory
        )

    def test_section_contains_course_faculty(self):
        self.cursor.fetchall.return_value = [
            (
                "CLS0000003",
                "MGT103.01",
                "SEM0000001",
                "MGT103",
                "Principles of Management",
                "LEC0000002",
                "Tran Hoang Nam",
                "B.303",
                4,
                time(13, 0),
                time(15, 30),
                40,
                1,
                "FAC0000002",
                "Business Administration",
            )
        ]

        sections = self.repo.list_sections(
            "SEM0000001"
        )

        self.assertEqual(len(sections), 1)
        self.assertEqual(
            sections[0]["courseFacultyId"],
            "FAC0000002",
        )
        self.assertEqual(
            sections[0]["courseFacultyName"],
            "Business Administration",
        )

        sql = self.cursor.execute.call_args.args[0]

        self.assertIn(
            "c.facultyId AS courseFacultyId",
            sql,
        )
        self.assertIn(
            "f.facultyName AS courseFacultyName",
            sql,
        )

    def test_existing_read_fixture_compatibility(self):
        self.cursor.fetchall.return_value = [
            (
                "CLS0000001",
                "DBI101.01",
                "SEM0000001",
                "DBI101",
                "Database Systems",
                "LEC0000001",
                "Nguyen Thi Lan",
                "A.101",
                2,
                time(7, 0),
                time(9, 30),
                40,
                3,
            )
        ]

        sections = self.repo.list_sections(
            "SEM0000001"
        )

        self.assertIsNone(
            sections[0]["courseFacultyId"]
        )
        self.assertIsNone(
            sections[0]["courseFacultyName"]
        )


if __name__ == "__main__":
    unittest.main()
