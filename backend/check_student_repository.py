
"""Local developer-only check of the StudentRepository against real SQL Server.

Run from backend/: python check_student_repository.py
Do not expose the resulting student directory via an unauthenticated API.
"""

import sys
import pyodbc

from app.repositories.database import DatabaseConfigurationError
from app.repositories.student_repository import StudentRepository


def main() -> int:
    try:
        repo = StudentRepository()
        students = repo.list_students(limit=10)

        print("=== SMS Group 05: StudentRepository integration check ===")
        print(
            f"Student records fetched: {len(students)} "
            "(first page, max 10)"
        )

        for student in students:
            # Don't print citizen IDs, birthdays or personal contact details.
            print(
                f"{student.studentId} | {student.fullName} | "
                f"{student.majorName} | {student.academicStatus}"
            )

        if students:
            selected = repo.get_student_by_id(
                students[0].studentId
            )

            assert selected is not None
            assert selected.studentId == students[0].studentId

            print("Parameterized lookup by studentId: OK")

        print(
            "SUCCESS: StudentRepository read queries "
            "work against SQL Server."
        )

        return 0

    except (
        DatabaseConfigurationError,
        pyodbc.Error,
        ValueError,
    ) as exc:
        print(
            f"REPOSITORY CHECK FAILED: {exc}",
            file=sys.stderr,
        )

        return 1


if __name__ == "__main__":
    raise SystemExit(main())
