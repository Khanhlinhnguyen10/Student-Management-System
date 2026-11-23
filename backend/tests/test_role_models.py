
import unittest
from dataclasses import fields
from datetime import date

from app.models.user import User
from app.models.administrator import Administrator
from app.models.student import Student
from app.models.lecturer import Lecturer


class RoleModelsTestCase(unittest.TestCase):

    def setUp(self):
        self.user_data = {
            "userId": "U00000000001",
            "username": "testuser",
            "passwordHash": "test-hash-value",
            "isLocked": False,
            "citizenId": "000000000001",
            "fullName": "Test User",
            "dateOfBirth": date(2004, 1, 1),
            "email": "test@example.com",
            "gender": "Female",
            "phoneNumber": "0123456789",
        }

    def make_roles(self):
        return [
            Administrator(**self.user_data, adminId="AD001"),
            Student(
                **self.user_data,
                studentId="ST001",
                majorId="M001",
                academicStatus="Active",
            ),
            Lecturer(
                **self.user_data,
                lecturerId="LT001",
                facultyId="F001",
            ),
        ]

    def test_administrator_inherits_user(self):
        administrator = self.make_roles()[0]

        self.assertIsInstance(administrator, User)
        self.assertEqual(administrator.adminId, "AD001")
        self.assertTrue(callable(administrator.createAccount))

    def test_student_inherits_user(self):
        student = self.make_roles()[1]

        self.assertIsInstance(student, User)
        self.assertEqual(student.studentId, "ST001")
        self.assertEqual(student.majorId, "M001")
        self.assertEqual(student.academicStatus, "Active")

    def test_lecturer_inherits_user(self):
        lecturer = self.make_roles()[2]

        self.assertIsInstance(lecturer, User)
        self.assertEqual(lecturer.lecturerId, "LT001")
        self.assertEqual(lecturer.facultyId, "F001")

    def test_role_ids_match_data_model(self):
        for cls, expected_fields in [
            (Administrator, {"adminId"}),
            (Student, {"studentId", "majorId", "academicStatus"}),
            (Lecturer, {"lecturerId", "facultyId"}),
        ]:
            with self.subTest(model=cls.__name__):
                names = {item.name for item in fields(cls)}

                self.assertTrue(expected_fields.issubset(names))
                self.assertIn("userId", names)

    def test_domain_operations_are_not_implemented_yet(self):
        administrator, student, lecturer = self.make_roles()

        operations = [
            administrator.createAccount,
            administrator.manageUsers,
            administrator.manageFaculties,
            administrator.manageCourses,
            administrator.manageSemesters,
            administrator.manageClassSections,
            student.updateContact,
            student.viewCurriculum,
            student.viewAcademicTranscript,
            lecturer.updateContact,
            lecturer.manageGrades,
        ]

        for operation in operations:
            with self.subTest(operation=operation.__name__):
                with self.assertRaises(NotImplementedError):
                    operation()

    def test_login_is_not_implemented_yet(self):
        for user in self.make_roles():
            with self.subTest(model=type(user).__name__):
                with self.assertRaises(NotImplementedError):
                    user.logIn("testuser", "example-password")

    def test_password_hash_hidden_from_subclass_repr(self):
        for user in self.make_roles():
            with self.subTest(model=type(user).__name__):
                self.assertNotIn("test-hash-value", repr(user))


if __name__ == "__main__":
    unittest.main()
