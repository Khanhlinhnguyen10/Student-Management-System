
"""Repository search tests: parameters rather than concatenated user SQL."""

import unittest
from unittest.mock import Mock

from app.repositories.student_repository import StudentRepository


class StudentSearchTests(unittest.TestCase):
    def setUp(self):
        self.cursor = Mock()
        self.conn = Mock()
        self.conn.cursor.return_value = self.cursor
        self.repo = StudentRepository(connection_factory=lambda: self.conn)

    def test_search_by_name_uses_bound_parameters(self):
        self.cursor.fetchall.return_value = []

        self.repo.list_students(
            search="Tran Minh",
            limit=10,
            offset=0,
        )

        sql, *params = self.cursor.execute.call_args.args

        self.assertIn("CHARINDEX(?, u.fullName)", sql)
        self.assertIn("CHARINDEX(?, s.studentId)", sql)
        self.assertNotIn("Tran Minh", sql)

        self.assertEqual(
            params,
            ["Tran Minh", "Tran Minh", 0, 10],
        )

    def test_search_with_sql_pattern_symbols_is_literal(self):
        self.cursor.fetchall.return_value = []

        self.repo.list_students(
            search="%_['",
            limit=10,
        )

        sql, *params = self.cursor.execute.call_args.args

        self.assertIn("CHARINDEX", sql)
        self.assertNotIn("LIKE", sql)

        self.assertEqual(
            params[:2],
            ["%_['", "%_['"],
        )

    def test_count_uses_same_filter(self):
        self.cursor.fetchone.return_value = (3,)

        total = self.repo.count_students(
            search="STU",
        )

        self.assertEqual(total, 3)

        sql, *params = self.cursor.execute.call_args.args

        self.assertIn("COUNT_BIG(*)", sql)

        self.assertEqual(
            params,
            ["STU", "STU"],
        )

        self.conn.rollback.assert_called_once()
        self.conn.close.assert_called_once()

    def test_empty_search_counts_all(self):
        self.cursor.fetchone.return_value = (9,)

        self.assertEqual(
            self.repo.count_students(),
            9,
        )

        self.assertEqual(
            len(self.cursor.execute.call_args.args),
            1,
        )

    def test_search_length_validation(self):
        with self.assertRaises(ValueError):
            self.repo.list_students(
                search="x" * 101,
            )

        with self.assertRaises(ValueError):
            self.repo.count_students(
                search=None,
            )


if __name__ == "__main__":
    unittest.main()
