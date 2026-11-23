
"""Unit tests for Administrator Faculty Management Service."""

import unittest
from unittest.mock import MagicMock

from app.services.admin_faculty_service import (
    AdminFacultyService,
)


VALID_FACULTY = {
    "facultyCode": "TESTFA",
    "facultyName": "Test Faculty",
    "email": "faculty@example.test",
    "phoneNumber": "0280000000",
}


class TestAdminFacultyService(unittest.TestCase):

    def setUp(self):
        self.repository = MagicMock()
        self.service = AdminFacultyService(
            repository=self.repository
        )

    def test_list_faculties(self):
        self.repository.list_faculties.return_value = []

        result = self.service.list_faculties()

        self.assertEqual(result, [])
        self.repository.list_faculties.assert_called_once()

    def test_get_faculty(self):
        self.repository.get_faculty.return_value = {
            "facultyId": "FAC0000901"
        }

        result = self.service.get_faculty(
            "FAC0000901"
        )

        self.assertEqual(
            result["facultyId"],
            "FAC0000901"
        )

    def test_create_faculty(self):
        self.repository.create_faculty.return_value = (
            "FAC0000903"
        )

        result = self.service.create_faculty(
            VALID_FACULTY
        )

        self.assertEqual(result, "FAC0000903")
        self.repository.create_faculty.assert_called_once()

    def test_create_normalizes_code(self):
        data = {
            **VALID_FACULTY,
            "facultyCode": "testfa",
        }

        self.service.create_faculty(data)

        payload = (
            self.repository.create_faculty.call_args.args[0]
        )

        self.assertEqual(
            payload["facultyCode"],
            "TESTFA"
        )

    def test_create_rejects_missing_name(self):
        data = {
            **VALID_FACULTY,
            "facultyName": "",
        }

        with self.assertRaises(ValueError):
            self.service.create_faculty(data)

        self.repository.create_faculty.assert_not_called()

    def test_create_rejects_invalid_email(self):
        data = {
            **VALID_FACULTY,
            "email": "invalid-email",
        }

        with self.assertRaises(ValueError):
            self.service.create_faculty(data)

        self.repository.create_faculty.assert_not_called()

    def test_create_rejects_invalid_phone(self):
        data = {
            **VALID_FACULTY,
            "phoneNumber": "abc123",
        }

        with self.assertRaises(ValueError):
            self.service.create_faculty(data)

        self.repository.create_faculty.assert_not_called()

    def test_update_faculty(self):
        data = {
            "facultyName": "Updated Faculty",
            "email": "updated@example.test",
            "phoneNumber": "0280000001",
        }

        self.repository.update_faculty.return_value = (
            "FAC0000903"
        )

        result = self.service.update_faculty(
            "FAC0000903",
            data,
        )

        self.assertEqual(result, "FAC0000903")
        self.repository.update_faculty.assert_called_once()

    def test_update_cannot_change_faculty_code(self):
        data = {
            **VALID_FACULTY,
        }

        with self.assertRaises(ValueError):
            self.service.update_faculty(
                "FAC0000903",
                data,
            )

        self.repository.update_faculty.assert_not_called()

    def test_delete_invalid_id(self):
        with self.assertRaises(ValueError):
            self.service.delete_faculty(
                "INVALID"
            )

        self.repository.delete_faculty.assert_not_called()


if __name__ == "__main__":
    unittest.main()
