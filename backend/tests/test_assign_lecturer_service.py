
"""Unit tests for Assign Lecturer Service - Group 05.

Use Case 40.

All database operations are mocked.
No SQL Server data is modified.
"""

import unittest
from unittest.mock import Mock

from app.repositories.assign_lecturer_repository import (
    AssignLecturerRepository,
    AssignmentBusyError,
    AssignmentNotFoundError,
    AssignmentScheduleConflictError,
)

from app.services.assign_lecturer_service import (
    AssignLecturerService,
    AssignLecturerValidationError,
)


VALID_ASSIGNMENT = {
    "classSectionId": "CLS0000005",
    "lecturerId": "LEC0000001",
}


class AssignLecturerServiceTests(unittest.TestCase):

    def setUp(self):
        self.repo = Mock(
            spec=AssignLecturerRepository
        )

        self.service = AssignLecturerService(
            repository=self.repo
        )

    # =====================================
    # LIST SEMESTERS
    # =====================================

    def test_list_semesters(self):
        expected = [
            {
                "semesterId": "SEM0000001",
                "semesterName": "Semester 1",
            }
        ]

        self.repo.list_semesters.return_value = expected

        result = self.service.list_semesters()

        self.assertEqual(result, expected)

        self.repo.list_semesters.assert_called_once()

    # =====================================
    # LIST LECTURERS
    # =====================================

    def test_list_lecturers(self):
        expected = [
            {
                "lecturerId": "LEC0000001",
                "fullName": "Test Lecturer",
            }
        ]

        self.repo.list_lecturers.return_value = expected

        result = self.service.list_lecturers()

        self.assertEqual(result, expected)

        self.repo.list_lecturers.assert_called_once()

    # =====================================
    # LIST CLASS SECTIONS
    # =====================================

    def test_list_sections(self):
        self.repo.list_sections.return_value = []

        result = self.service.list_sections(
            " SEM0000001 "
        )

        self.assertEqual(result, [])

        self.repo.list_sections.assert_called_once_with(
            "SEM0000001"
        )

    def test_reject_invalid_semester(self):
        for value in (
            "",
            "   ",
            None,
            123,
            "SEM000000123456",
        ):
            with self.subTest(value=value):
                with self.assertRaises(
                    AssignLecturerValidationError
                ):
                    self.service.list_sections(value)

        self.repo.list_sections.assert_not_called()

    # =====================================
    # SUCCESSFUL ASSIGNMENT
    # =====================================

    def test_assign_valid_payload(self):
        expected = {
            "classSectionId": "CLS0000005",
            "classCode": "TEST.01",
            "semesterId": "SEM0000001",
            "lecturerId": "LEC0000001",
            "changed": True,
        }

        self.repo.assign_lecturer.return_value = expected

        result = self.service.assign_record({
            "classSectionId": " CLS0000005 ",
            "lecturerId": " LEC0000001 ",
        })

        self.assertEqual(result, expected)

        self.repo.assign_lecturer.assert_called_once_with(
            class_section_id="CLS0000005",
            lecturer_id="LEC0000001",
        )

    # =====================================
    # INVALID INPUT
    # =====================================

    def test_reject_non_dictionary(self):
        with self.assertRaises(
            AssignLecturerValidationError
        ):
            self.service.assign_record(
                "invalid"
            )

        self.repo.assign_lecturer.assert_not_called()

    def test_reject_missing_field(self):
        with self.assertRaises(
            AssignLecturerValidationError
        ):
            self.service.assign_record({
                "classSectionId": "CLS0000005"
            })

        self.repo.assign_lecturer.assert_not_called()

    def test_reject_unsupported_fields(self):
        with self.assertRaises(
            AssignLecturerValidationError
        ):
            self.service.assign_record({
                **VALID_ASSIGNMENT,
                "semesterId": "SEM0000001",
            })

        self.repo.assign_lecturer.assert_not_called()

    def test_reject_invalid_identifiers(self):
        invalid_payloads = [
            {
                "classSectionId": "",
                "lecturerId": "LEC0000001",
            },
            {
                "classSectionId": "CLS0000005",
                "lecturerId": "",
            },
            {
                "classSectionId": "CLS0000005",
                "lecturerId": "LEC123456789",
            },
            {
                "classSectionId": 123,
                "lecturerId": "LEC0000001",
            },
        ]

        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                with self.assertRaises(
                    AssignLecturerValidationError
                ):
                    self.service.assign_record(payload)

        self.repo.assign_lecturer.assert_not_called()

    # =====================================
    # CONFLICT ERROR
    # =====================================

    def test_schedule_conflict_propagates(self):
        self.repo.assign_lecturer.side_effect = (
            AssignmentScheduleConflictError(
                "Teaching schedule conflict with TEST.02."
            )
        )

        with self.assertRaises(
            AssignmentScheduleConflictError
        ):
            self.service.assign_record(
                VALID_ASSIGNMENT
            )

    # =====================================
    # RECORD NOT FOUND
    # =====================================

    def test_not_found_propagates(self):
        self.repo.assign_lecturer.side_effect = (
            AssignmentNotFoundError(
                "Lecturer does not exist."
            )
        )

        with self.assertRaises(
            AssignmentNotFoundError
        ):
            self.service.assign_record(
                VALID_ASSIGNMENT
            )

    # =====================================
    # TRANSACTION BUSY
    # =====================================

    def test_busy_propagates(self):
        self.repo.assign_lecturer.side_effect = (
            AssignmentBusyError(
                "Assignment is busy."
            )
        )

        with self.assertRaises(
            AssignmentBusyError
        ):
            self.service.assign_record(
                VALID_ASSIGNMENT
            )


if __name__ == "__main__":
    unittest.main()
