
"""Unit tests for Lecturer Gradebook authorization.

Tests use mocked database connections.
No real SQL Server data is modified.
"""

import unittest
from unittest.mock import MagicMock, patch

from app.repositories.lecturer_gradebook_repository import (
    ACCESS_SQL,
    LecturerGradebookRepository,
)


USER_ID = "USR0000901"
SECTION_ID = "CLS0000914"
ENROLLMENT_ID = "ENR0000906"
GRADEBOOK_ID = "GRB0000906"
TOKEN_HASH = "a" * 64

MARKS = {
    "midtermMark": 8.0,
    "assignmentMark": 8.5,
    "attendanceMark": 9.0,
    "finalExamMark": 8.0,
}


class TestLecturerGradebookPermissions(unittest.TestCase):

    def setUp(self):
        self.cursor = MagicMock()
        self.connection = MagicMock()

        self.connection.cursor.return_value = self.cursor

        self.context = MagicMock()
        self.context.__enter__.return_value = (
            self.connection
        )

        self.patcher = patch(
            "app.repositories."
            "lecturer_gradebook_repository."
            "connection_scope",
            return_value=self.context,
        )

        self.patcher.start()
        self.addCleanup(self.patcher.stop)

        self.repository = LecturerGradebookRepository()

    def assert_no_database_write(self):
        """Verify no INSERT, UPDATE or procedure execution."""

        for call in self.cursor.execute.call_args_list:
            sql = call.args[0].strip().upper()

            self.assertFalse(
                sql.startswith(
                    ("INSERT", "UPDATE", "DELETE", "EXEC")
                ),
                f"Unexpected database write: {sql}",
            )

    # -----------------------------------------
    # TEST 1 - Authorization query
    # -----------------------------------------

    def test_access_query_checks_lecturer_ownership(self):
        self.assertIn(
            "e.enrollmentId = ?",
            ACCESS_SQL,
        )

        self.assertIn(
            "e.classSectionId = ?",
            ACCESS_SQL,
        )

        self.assertIn(
            "l.userId = ?",
            ACCESS_SQL,
        )

    # -----------------------------------------
    # TEST 2 - Unauthorized Gradebook GET
    # -----------------------------------------

    def test_cannot_read_unassigned_class(self):
        self.cursor.fetchone.return_value = None

        result = self.repository.get_section_gradebook(
            USER_ID,
            SECTION_ID,
        )

        self.assertIsNone(result)

        self.assertEqual(
            self.cursor.execute.call_count,
            1,
        )

        self.assert_no_database_write()

    # -----------------------------------------
    # TEST 3 - Unauthorized Save Draft
    # -----------------------------------------

    def test_cannot_save_draft_for_unassigned_class(self):
        self.cursor.fetchone.return_value = None

        with self.assertRaises(LookupError):
            self.repository.save_draft(
                USER_ID,
                SECTION_ID,
                ENROLLMENT_ID,
                MARKS,
            )

        self.assertEqual(
            self.cursor.execute.call_count,
            1,
        )

        self.assert_no_database_write()

    # -----------------------------------------
    # TEST 4 - Unauthorized Finalize
    # -----------------------------------------

    def test_cannot_finalize_unassigned_class(self):
        self.cursor.fetchone.side_effect = [
            ("LEC0000901",),
            None,
        ]

        with self.assertRaises(LookupError):
            self.repository.save_final(
                USER_ID,
                TOKEN_HASH,
                SECTION_ID,
                ENROLLMENT_ID,
                MARKS,
            )

        self.assertEqual(
            self.cursor.execute.call_count,
            2,
        )

        self.assert_no_database_write()

    # -----------------------------------------
    # TEST 5 - Finalized Draft Protection
    # -----------------------------------------

    def test_cannot_overwrite_finalized_draft(self):
        self.cursor.fetchone.return_value = (
            GRADEBOOK_ID,
            1,
        )

        with self.assertRaises(PermissionError):
            self.repository.save_draft(
                USER_ID,
                SECTION_ID,
                ENROLLMENT_ID,
                MARKS,
            )

        self.assert_no_database_write()

    # -----------------------------------------
    # TEST 6 - Finalized Grade Protection
    # -----------------------------------------

    def test_cannot_modify_finalized_grade(self):
        self.cursor.fetchone.side_effect = [
            ("LEC0000901",),
            (GRADEBOOK_ID, 1),
        ]

        with self.assertRaises(PermissionError):
            self.repository.save_final(
                USER_ID,
                TOKEN_HASH,
                SECTION_ID,
                ENROLLMENT_ID,
                MARKS,
            )

        self.assert_no_database_write()


if __name__ == "__main__":
    unittest.main()
