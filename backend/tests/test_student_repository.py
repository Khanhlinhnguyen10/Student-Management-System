
"""SQL query composition, mapping and read transaction tests without SQL Server."""

from datetime import date
import unittest
from unittest.mock import Mock

from app.repositories.student_repository import StudentRepository


_ROW = (
    "STU0000001",
    "079000000002",
    "Tran Minh Anh",
    date(2004, 2, 1),
    "demo@example.test",
    "Female",
    "0900000002",
    "Information Technology",
    "Computer Science",
    "Active",
)


class StudentRepositoryTests(unittest.TestCase):

    def setUp(self):
        self.cursor = Mock()
        self.conn = Mock()
        self.conn.cursor.return_value = self.cursor
        self.factory = Mock(return_value=self.conn)
        self.repo = StudentRepository(
            connection_factory=self.factory
        )

    def test_list_maps_joined_student_columns(self):
        self.cursor.fetchall.return_value = [_ROW]

        students = self.repo.list_students(
            limit=5,
            offset=0,
        )

        self.assertEqual(len(students), 1)
        self.assertEqual(
            students[0].studentId,
            "STU0000001",
        )
        self.assertEqual(
            students[0].fullName,
            "Tran Minh Anh",
        )
        self.assertEqual(
            students[0].majorName,
            "Computer Science",
        )
        self.assertEqual(
            students[0].academicStatus,
            "Active",
        )
        self.assertEqual(
            students[0].dateOfBirth,
            date(2004, 2, 1),
        )

        self.conn.rollback.assert_called_once_with()
        self.conn.commit.assert_not_called()
        self.conn.close.assert_called_once_with()
        self.cursor.close.assert_called_once_with()

    def test_list_uses_sql_parameters_for_pagination(self):
        self.cursor.fetchall.return_value = []

        self.repo.list_students(
            limit=8,
            offset=12,
        )

        args = self.cursor.execute.call_args.args

        self.assertIn(
            "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY",
            args[0],
        )

        self.assertIn("dbo.Students", args[0])
        self.assertIn("dbo.Users", args[0])
        self.assertIn("dbo.Majors", args[0])
        self.assertIn("dbo.Faculties", args[0])

        self.assertEqual(
            args[1:],
            (12, 8),
        )

    def test_get_student_by_id_uses_bound_parameter(self):
        self.cursor.fetchone.return_value = _ROW

        student = self.repo.get_student_by_id(
            "STU0000001"
        )

        self.assertEqual(
            student.fullName,
            "Tran Minh Anh",
        )

        args = self.cursor.execute.call_args.args

        self.assertIn(
            "WHERE s.studentId = ?",
            args[0],
        )
        self.assertEqual(
            args[1:],
            ("STU0000001",),
        )

        self.conn.rollback.assert_called_once_with()

    def test_get_student_by_id_returns_none_if_missing(self):
        self.cursor.fetchone.return_value = None

        result = self.repo.get_student_by_id(
            "STU0000099"
        )

        self.assertIsNone(result)
        self.conn.close.assert_called_once_with()

    def test_empty_list_is_valid(self):
        self.cursor.fetchall.return_value = []

        result = self.repo.list_students()

        self.assertEqual(result, [])

    def test_invalid_limit_is_rejected_without_connection(self):
        for limit in (0, 101, -1, True, "10"):
            with self.subTest(limit=limit):
                with self.assertRaises(ValueError):
                    self.repo.list_students(limit=limit)

        self.factory.assert_not_called()

    def test_invalid_offset_is_rejected_without_connection(self):
        for offset in (-1, True, "0"):
            with self.subTest(offset=offset):
                with self.assertRaises(ValueError):
                    self.repo.list_students(offset=offset)

        self.factory.assert_not_called()

    def test_invalid_student_id_is_rejected_without_connection(self):
        for student_id in (
            "",
            " ",
            "TOO_LONG_STUDENT_ID",
            None,
            123,
        ):
            with self.subTest(student_id=student_id):
                with self.assertRaises(ValueError):
                    self.repo.get_student_by_id(
                        student_id
                    )

        self.factory.assert_not_called()

    def test_sql_exception_rolls_back_and_closes(self):
        self.cursor.execute.side_effect = RuntimeError(
            "SQL execution failed"
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "SQL execution failed",
        ):
            self.repo.list_students()

        self.conn.rollback.assert_called_once_with()
        self.conn.close.assert_called_once_with()
        self.cursor.close.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
