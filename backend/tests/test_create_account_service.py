
"""Unit tests for Group 05 - Use Case 11: Create Account.

Tests validate the CreateAccountService for:
- Student account creation
- Lecturer account creation
- Required fields
- Invalid inputs
- Initial password generation
- Existing password hashing compatibility
- Duplicate identity handling

All database interactions use mocks.
No real SQL Server records are modified.
"""

import re
import unittest
from unittest.mock import Mock

from werkzeug.security import check_password_hash

from app.repositories.create_account_repository import (
    AccountAlreadyExistsError,
)

from app.services.create_account_service import (
    CreateAccountService,
    CreateAccountValidationError,
)


# =========================================
# TEST INPUT DATA
# =========================================

STUDENT_DATA = {
    "accountType": "Student",
    "username": "student_test01",
    "citizenId": "079000001234",
    "fullName": "Test Student",
    "dateOfBirth": "2005-04-15",
    "email": "student@example.test",
    "phoneNumber": "0901234567",
    "gender": "Female",
    "majorId": "MAJ0000001",
    "academicStatus": "Active",
}

LECTURER_DATA = {
    "accountType": "Lecturer",
    "username": "lecturer_test01",
    "citizenId": "079000005678",
    "fullName": "Test Lecturer",
    "dateOfBirth": "1985-03-12",
    "email": "lecturer@example.test",
    "phoneNumber": "0909876543",
    "gender": "Male",
    "facultyId": "FAC0000001",
}


class CreateAccountServiceTests(unittest.TestCase):

    def setUp(self):
        """Use a mock Repository instead of SQL Server."""

        self.repository = Mock()

        self.repository.create_account.return_value = {
            "accountType": "Student",
            "userId": "USR000000007",
            "username": "student_test01",
            "studentId": "STU0000004",
            "lecturerId": None,
        }

        self.service = CreateAccountService(
            repository=self.repository
        )

    # =========================================
    # TEST 01 - CREATE STUDENT
    # =========================================

    def test_create_student(self):

        result = self.service.create_record(
            STUDENT_DATA
        )

        kwargs = (
            self.repository.create_account
            .call_args.kwargs
        )

        self.assertEqual(
            result["account"]["studentId"],
            "STU0000004",
        )

        self.assertEqual(
            kwargs["account_type"],
            "Student",
        )

        self.assertEqual(
            kwargs["major_id"],
            "MAJ0000001",
        )

        self.assertEqual(
            kwargs["academic_status"],
            "Active",
        )

        self.assertNotIn(
            "faculty_id",
            kwargs,
        )

        self.assertTrue(
            check_password_hash(
                kwargs["password_hash"],
                result["initialCredentials"][
                    "initialPassword"
                ],
            )
        )

    # =========================================
    # TEST 02 - CREATE LECTURER
    # =========================================

    def test_create_lecturer(self):

        self.repository.create_account.return_value = {
            "accountType": "Lecturer",
            "userId": "USR000000008",
            "username": "lecturer_test01",
            "studentId": None,
            "lecturerId": "LEC0000003",
        }

        result = self.service.create_record(
            LECTURER_DATA
        )

        kwargs = (
            self.repository.create_account
            .call_args.kwargs
        )

        self.assertEqual(
            result["account"]["lecturerId"],
            "LEC0000003",
        )

        self.assertEqual(
            kwargs["account_type"],
            "Lecturer",
        )

        self.assertEqual(
            kwargs["faculty_id"],
            "FAC0000001",
        )

        self.assertNotIn(
            "major_id",
            kwargs,
        )

    # =========================================
    # TEST 03 - INVALID ACCOUNT TYPE
    # =========================================

    def test_reject_invalid_account_type(self):

        payload = {
            **STUDENT_DATA,
            "accountType": "Administrator",
        }

        with self.assertRaises(
            CreateAccountValidationError
        ):
            self.service.create_record(
                payload
            )

        self.repository.create_account.assert_not_called()

    # =========================================
    # TEST 04 - PROTECTED EXTRA FIELD
    # =========================================

    def test_reject_unsupported_fields(self):

        payload = {
            **STUDENT_DATA,
            "userId": "USR999999999",
        }

        with self.assertRaises(
            CreateAccountValidationError
        ):
            self.service.create_record(
                payload
            )

        self.repository.create_account.assert_not_called()

    # =========================================
    # TEST 05 - REQUIRED STUDENT STATUS
    # =========================================

    def test_student_requires_academic_status(self):

        payload = dict(STUDENT_DATA)

        payload.pop("academicStatus")

        with self.assertRaises(
            CreateAccountValidationError
        ):
            self.service.create_record(
                payload
            )

        self.repository.create_account.assert_not_called()

    # =========================================
    # TEST 06 - REQUIRED LECTURER FACULTY
    # =========================================

    def test_lecturer_requires_faculty(self):

        payload = dict(LECTURER_DATA)

        payload.pop("facultyId")

        with self.assertRaises(
            CreateAccountValidationError
        ):
            self.service.create_record(
                payload
            )

        self.repository.create_account.assert_not_called()

    # =========================================
    # TEST 07 - INVALID DATE
    # =========================================

    def test_reject_invalid_date(self):

        payload = {
            **STUDENT_DATA,
            "dateOfBirth": "2026-13-40",
        }

        with self.assertRaises(
            CreateAccountValidationError
        ):
            self.service.create_record(
                payload
            )

        self.repository.create_account.assert_not_called()

    # =========================================
    # TEST 08 - INVALID EMAIL
    # =========================================

    def test_reject_invalid_email(self):

        payload = {
            **LECTURER_DATA,
            "email": "invalid-email",
        }

        with self.assertRaises(
            CreateAccountValidationError
        ):
            self.service.create_record(
                payload
            )

        self.repository.create_account.assert_not_called()

    # =========================================
    # TEST 09 - DUPLICATE UNIQUE FIELD
    # =========================================

    def test_duplicate_identity_error_propagates(self):

        self.repository.create_account.side_effect = (
            AccountAlreadyExistsError(
                "Username already exists."
            )
        )

        with self.assertRaises(
            AccountAlreadyExistsError
        ):
            self.service.create_record(
                STUDENT_DATA
            )

    # =========================================
    # TEST 10 - INITIAL PASSWORD
    # =========================================

    def test_initial_password_meets_existing_policy(self):

        password = (
            self.service._generate_initial_password()
        )

        self.assertGreaterEqual(
            len(password),
            8,
        )

        self.assertLessEqual(
            len(password),
            128,
        )

        self.assertRegex(
            password,
            r"[A-Z]",
        )

        self.assertRegex(
            password,
            r"[a-z]",
        )

        self.assertRegex(
            password,
            r"\d",
        )

        self.assertTrue(
            re.search(
                r"[^A-Za-z0-9]",
                password,
            )
        )


if __name__ == "__main__":
    unittest.main()
