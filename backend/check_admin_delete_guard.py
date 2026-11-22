
"""Verify student deletion protection against real SQL Server data.

This test must not delete the student because related records exist.
"""

from app.repositories.student_repository import (
    StudentRepository,
    StudentDataIntegrityError,
)


def main():
    student_id = "STU0000001"

    repository = StudentRepository()

    print("=== Group 05: Student DELETE integrity check ===")
    print(f"Student ID: {student_id}")

    try:
        deleted = repository.delete_student(student_id)

    except StudentDataIntegrityError as exc:
        print("\nPASS: DELETE was correctly blocked.")
        print(f"Reason: {exc}")

    else:
        if deleted:
            raise RuntimeError(
                "UNSAFE: Student was unexpectedly deleted."
            )

        raise RuntimeError(
            "Student was not found. Check the database."
        )

    # Verify that the student still exists.
    student = repository.get_student_by_id(student_id)

    if student is None:
        raise RuntimeError(
            "FAIL: Student record was not preserved."
        )

    print("\nPASS: Student record still exists.")
    print(f"Student name: {student.fullName}")

    print("\nSUCCESS: SQL Server deletion protection verified.")


if __name__ == "__main__":
    main()
