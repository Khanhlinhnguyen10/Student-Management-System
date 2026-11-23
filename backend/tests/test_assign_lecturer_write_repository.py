
"""Tests for assigning lecturers to class sections.

Group 05 - Use Case 40.

Tests:
- Successful assignment
- Schedule conflict
- Missing class section
- Missing lecturer
- Incomplete target schedule
- Incomplete existing schedule
- Lock acquisition failure
- Idempotent assignment

No real SQL connection is created.
"""

import unittest
from contextlib import contextmanager
from datetime import time
from unittest.mock import MagicMock, patch

from app.repositories.assign_lecturer_repository import (
    AssignLecturerRepository,
    AssignmentBusyError,
    AssignmentNotFoundError,
    AssignmentScheduleConflictError,
    AssignmentScheduleError,
)


class AssignLecturerWriteTests(unittest.TestCase):

    def setUp(self):
        self.connection = MagicMock()
        self.cursor = self.connection.cursor.return_value

        self.cursor.description = [
            ("lockResult",)
        ]
        self.cursor.rowcount = 1

        self.factory = MagicMock(
            return_value=self.connection
        )

        self.repo = AssignLecturerRepository(
            connection_factory=self.factory
        )

        self.scope_patch = patch(
            "app.repositories.assign_lecturer_repository"
            ".connection_scope",
            self._fake_connection_scope,
        )
        self.scope_patch.start()
        self.addCleanup(self.scope_patch.stop)

    @contextmanager
    def _fake_connection_scope(
        self,
        *,
        write=False,
        connection_factory=None,
    ):
        self.assertTrue(write)

        connection = connection_factory()

        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    @staticmethod
    def _section(current_lecturer=None):
        return (
            "CLS0000005",
            "DBI101.03",
            "SEM0000001",
            current_lecturer,
            2,
            time(7, 0),
            time(9, 30),
        )

    def _set_queries(
        self,
        *,
        lock_result=0,
        section=None,
        lecturer=("LEC0000001",),
        incomplete=None,
        conflict=None,
    ):
        if section is None:
            section = self._section()

        self.cursor.fetchone.side_effect = [
            (lock_result,),
            section,
            lecturer,
            incomplete,
            conflict,
        ]

    def _assign(self):
        return self.repo.assign_lecturer(
            class_section_id="CLS0000005",
            lecturer_id="LEC0000001",
        )

    # =========================================
    # SUCCESS
    # =========================================

    def test_successful_assignment(self):
        self._set_queries()

        result = self._assign()

        self.assertTrue(result["changed"])
        self.assertEqual(
            result["lecturerId"],
            "LEC0000001",
        )

        queries = [
            call.args[0]
            for call in self.cursor.execute.call_args_list
        ]

        self.assertTrue(
            any("sp_getapplock" in q for q in queries)
        )

        self.assertTrue(
            any(
                "UPDATE dbo.ClassSections" in q
                for q in queries
            )
        )

        self.connection.commit.assert_called_once()
        self.connection.rollback.assert_not_called()
        self.connection.close.assert_called_once()
        self.cursor.close.assert_called_once()

    # =========================================
    # SCHEDULE CONFLICT
    # =========================================

    def test_conflicting_schedule_rejected(self):
        self._set_queries(
            conflict=(
                "PRG102.02",
                2,
                time(8, 0),
                time(10, 0),
            )
        )

        with self.assertRaises(
            AssignmentScheduleConflictError
        ) as caught:
            self._assign()

        self.assertIn(
            "PRG102.02",
            str(caught.exception),
        )
        self.assertIn(
            "08:00-10:00",
            str(caught.exception),
        )

        self.connection.commit.assert_not_called()
        self.connection.rollback.assert_called_once()

    # =========================================
    # CLASS SECTION NOT FOUND
    # =========================================

    def test_missing_class_section(self):
        self.cursor.fetchone.side_effect = [
            (0,),
            None,
        ]

        with self.assertRaises(
            AssignmentNotFoundError
        ):
            self._assign()

        self.connection.rollback.assert_called_once()
        self.connection.commit.assert_not_called()

    # =========================================
    # LECTURER NOT FOUND
    # =========================================

    def test_missing_lecturer(self):
        self.cursor.fetchone.side_effect = [
            (0,),
            self._section(),
            None,
        ]

        with self.assertRaises(
            AssignmentNotFoundError
        ):
            self._assign()

        self.connection.rollback.assert_called_once()
        self.connection.commit.assert_not_called()

    # =========================================
    # MISSING TARGET SCHEDULE
    # =========================================

    def test_incomplete_target_schedule(self):
        section = (
            "CLS0000005",
            "DBI101.03",
            "SEM0000001",
            None,
            2,
            None,
            time(9, 30),
        )

        self.cursor.fetchone.side_effect = [
            (0,),
            section,
        ]

        with self.assertRaises(
            AssignmentScheduleError
        ):
            self._assign()

        self.connection.rollback.assert_called_once()

    # =========================================
    # MISSING EXISTING SCHEDULE
    # =========================================

    def test_incomplete_existing_schedule(self):
        self._set_queries(
            incomplete=(
                "PRG102.02",
                None,
                None,
                None,
            )
        )

        with self.assertRaises(
            AssignmentScheduleError
        ) as caught:
            self._assign()

        self.assertIn(
            "PRG102.02",
            str(caught.exception),
        )

        self.connection.rollback.assert_called_once()

    # =========================================
    # TRANSACTION LOCK FAILURE
    # =========================================

    def test_assignment_lock_failure(self):
        self.cursor.fetchone.side_effect = [
            (-1,),
        ]

        with self.assertRaises(
            AssignmentBusyError
        ):
            self._assign()

        self.connection.rollback.assert_called_once()
        self.connection.commit.assert_not_called()

    # =========================================
    # IDEMPOTENT ASSIGNMENT
    # =========================================

    def test_already_assigned_same_lecturer(self):
        self._set_queries(
            section=self._section(
                current_lecturer="LEC0000001"
            )
        )

        result = self._assign()

        self.assertFalse(result["changed"])

        queries = [
            call.args[0]
            for call in self.cursor.execute.call_args_list
        ]

        self.assertFalse(
            any(
                "UPDATE dbo.ClassSections" in q
                for q in queries
            )
        )

        self.connection.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
