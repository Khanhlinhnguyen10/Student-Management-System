
"""Tests for Assign Lecturer read-only Repository.

Use Case 40 - Group 05.
No real SQL Server connections are created.
"""

import unittest
from datetime import date, time
from unittest.mock import MagicMock

from app.repositories.assign_lecturer_repository import (
    AssignLecturerRepository,
)


class AssignLecturerRepositoryTests(unittest.TestCase):

    def setUp(self):
        self.connection = MagicMock()
        self.cursor = self.connection.cursor.return_value

        self.factory = MagicMock(
            return_value=self.connection
        )

        self.repository = AssignLecturerRepository(
            connection_factory=self.factory
        )

    def test_list_semesters(self):
        self.cursor.fetchall.return_value = [
            (
                "SEM0000001",
                "Semester 1",
                "2025-2026",
                date(2025, 9, 1),
                date(2026, 1, 15),
            )
        ]

        result = self.repository.list_semesters()

        self.assertEqual(len(result), 1)
        self.assertEqual(
            result[0]["semesterId"],
            "SEM0000001",
        )
        self.assertEqual(
            result[0]["startDate"],
            "2025-09-01",
        )

        self.cursor.close.assert_called_once()
        self.connection.close.assert_called_once()

    def test_list_sections_filters_by_semester(self):
        self.cursor.fetchall.return_value = [
            (
                "CLS0000001",
                "DBI101.01",
                "SEM0000001",
                "DBI101",
                "Database Systems",
                "LEC0000001",
                "Test Lecturer",
                "A.101",
                2,
                time(7, 0),
                time(9, 30),
                40,
                3,
            )
        ]

        result = self.repository.list_sections(
            "SEM0000001"
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(
            result[0]["classSectionId"],
            "CLS0000001",
        )
        self.assertEqual(
            result[0]["startTime"],
            "07:00",
        )
        self.assertEqual(
            result[0]["endTime"],
            "09:30",
        )

        sql, semester_id = (
            self.cursor.execute.call_args.args
        )

        self.assertIn(
            "WHERE cs.semesterId = ?",
            sql,
        )
        self.assertEqual(
            semester_id,
            "SEM0000001",
        )

    def test_list_lecturers(self):
        self.cursor.fetchall.return_value = [
            (
                "LEC0000001",
                "Test Lecturer",
                "FAC0000001",
                "Information Technology",
            )
        ]

        result = self.repository.list_lecturers()

        self.assertEqual(len(result), 1)
        self.assertEqual(
            result[0]["lecturerId"],
            "LEC0000001",
        )
        self.assertEqual(
            result[0]["facultyId"],
            "FAC0000001",
        )

        self.cursor.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
