
"""Verify Administrator student UPDATE against real SQL Server.

Uses the existing values of student01.
No personal information is intentionally changed.
"""

from app.repositories.student_repository import StudentRepository
from app.services.admin_student_service import AdminStudentService


def main():
    student_id = "STU0000001"

    repository = StudentRepository()
    service = AdminStudentService(repository=repository)

    print("=== Group 05: SQL Server Student UPDATE test ===")
    print(f"Student ID: {student_id}")

    # 1. Read original student record.
    before = repository.get_student_by_id(student_id)

    if before is None:
        raise RuntimeError("Student record not found.")

    if not before.majorId:
        raise RuntimeError(
            "Major ID is unavailable. Check StudentRecord mapping."
        )

    print(f"Student: {before.fullName}")
    print(f"Major ID: {before.majorId}")

    # 2. Build an update payload using existing values.
    payload = {
        "citizenId": before.citizenId,
        "fullName": before.fullName,
        "dateOfBirth": (
            before.dateOfBirth.isoformat()
            if before.dateOfBirth else None
        ),
        "email": before.email,
        "gender": before.gender,
        "phoneNumber": before.phoneNumber,
        "majorId": before.majorId,
        "academicStatus": before.academicStatus,
    }

    # 3. Execute UPDATE through the Service and Repository.
    updated = service.update_record(
        student_id,
        payload,
    )

    print("\nPASS: UPDATE operation executed.")
    print(f"Updated student: {updated['fullName']}")

    # 4. Read again using a new SQL connection.
    after = repository.get_student_by_id(student_id)

    if after is None:
        raise RuntimeError(
            "Student record disappeared after UPDATE."
        )

    # 5. Verify that all existing values are preserved.
    fields = (
        "studentId",
        "citizenId",
        "fullName",
        "dateOfBirth",
        "email",
        "gender",
        "phoneNumber",
        "majorName",
        "academicStatus",
        "majorId",
    )

    for field in fields:
        if getattr(before, field) != getattr(after, field):
            raise RuntimeError(
                f"Data verification failed: {field} changed."
            )

    print("PASS: All original student values are preserved.")
    print("PASS: Data verified using a new SQL connection.")

    print("\nSUCCESS: SQL Server UPDATE transaction verified.")


if __name__ == "__main__":
    main()
