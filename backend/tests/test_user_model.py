
import inspect
import unittest
from dataclasses import fields
from datetime import date

from app.models.user import User
from app.models.student import Student


class UserModelTestCase(unittest.TestCase):

    def setUp(self):
        self.user_data = {
            "userId": "U00000000001",
            "username": "student_test",
            "passwordHash": "example-hash-value",
            "isLocked": False,
            "citizenId": "000000000001",
            "fullName": "Test Student",
            "dateOfBirth": date(2005, 3, 15),
            "email": "student@example.com",
            "gender": "Female",
            "phoneNumber": "0123456789",
        }

    def test_user_cannot_be_instantiated_directly(self):
        with self.assertRaises(TypeError):
            User(**self.user_data)

    def test_user_is_a_real_abstract_class(self):
        self.assertTrue(inspect.isabstract(User))

    def test_user_attributes_match_class_diagram(self):
        expected_attributes = [
            "userId", "username", "passwordHash", "isLocked",
            "citizenId", "fullName", "dateOfBirth", "email",
            "gender", "phoneNumber",
        ]

        self.assertEqual(
            [item.name for item in fields(User)],
            expected_attributes
        )

    def test_password_hash_is_hidden_from_repr(self):
        student = Student(
            **self.user_data,
            studentId="ST001",
            majorId="M001",
            academicStatus="Active",
        )

        self.assertNotIn("example-hash-value", repr(student))

    def test_nullable_user_columns_accept_none(self):
        nullable_data = self.user_data | {
            "dateOfBirth": None,
            "email": None,
            "gender": None,
            "phoneNumber": None,
        }

        student = Student(
            **nullable_data,
            studentId="ST001",
            majorId="M001",
            academicStatus="Active",
        )

        self.assertIsNone(student.dateOfBirth)
        self.assertIsNone(student.email)
        self.assertIsNone(student.gender)
        self.assertIsNone(student.phoneNumber)


if __name__ == "__main__":
    unittest.main()
