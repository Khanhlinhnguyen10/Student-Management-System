
"""Read-only SQL Server integration check for SMS Group 05."""

import sys
import pyodbc

from app.repositories.database import (
    DatabaseConfigurationError,
    DatabaseSettings,
    get_connection,
)


EXPECTED_TABLES = {
    "Users",
    "Administrators",
    "Students",
    "Lecturers",
    "Faculties",
    "Majors",
    "Semesters",
    "Courses",
    "Curriculum",
    "CurriculumCourses",
    "CoursePrerequisites",
    "ClassSections",
    "Enrollments",
    "GradeBooks",
    "SemesterResults",
    "UserSessions",
    "GradeScales",
}

EXPECTED_PROCEDURES = {
    "usp_CreateUserSession",
    "usp_TouchUserSession",
    "usp_RevokeUserSession",
    "usp_RecalculateStudentGPA",
    "usp_FinalizeGradeBook",
}


def main() -> int:
    try:
        settings = DatabaseSettings.from_environment()

        print("=== SMS Group 05: SQL Server integration check ===")
        print(f"Server: {settings.server}")
        print(f"Database: {settings.database}")
        print(f"Driver: {settings.driver}")
        print(f"Authentication: {settings.auth_mode}")
        print("Credentials: [hidden]")

        conn = get_connection()

        try:
            cursor = conn.cursor()

            actual_database = cursor.execute(
                "SELECT DB_NAME()"
            ).fetchone()[0]

            print(f"Connected to database: {actual_database}")

            tables = {
                row[0]
                for row in cursor.execute(
                    "SELECT name FROM sys.tables "
                    "WHERE schema_id = SCHEMA_ID(N'dbo')"
                ).fetchall()
            }

            missing_tables = sorted(EXPECTED_TABLES - tables)

            print(
                f"Expected tables present: "
                f"{len(EXPECTED_TABLES) - len(missing_tables)}/17"
            )

            if missing_tables:
                print("Missing tables:", ", ".join(missing_tables))

            procedures = {
                row[0]
                for row in cursor.execute(
                    "SELECT name FROM sys.procedures "
                    "WHERE schema_id = SCHEMA_ID(N'dbo')"
                ).fetchall()
            }

            missing_procedures = sorted(
                EXPECTED_PROCEDURES - procedures
            )

            print(
                f"Expected procedures present: "
                f"{len(EXPECTED_PROCEDURES) - len(missing_procedures)}/5"
            )

            if missing_procedures:
                print(
                    "Missing procedures:",
                    ", ".join(missing_procedures)
                )

            if not missing_tables:
                for table in (
                    "Users",
                    "Courses",
                    "GradeBooks",
                    "GradeScales",
                    "UserSessions",
                ):
                    count = cursor.execute(
                        f"SELECT COUNT_BIG(*) FROM dbo.{table}"
                    ).fetchone()[0]

                    print(f"dbo.{table}: {count} records")

            if missing_tables or missing_procedures:
                print("CHECK INCOMPLETE: SQL schema is missing objects.")
                return 1

            print(
                "SUCCESS: SQL Server connection "
                "and read-only queries work."
            )

            return 0

        finally:
            conn.close()

    except DatabaseConfigurationError as exc:
        print(f"CONFIGURATION ERROR: {exc}", file=sys.stderr)
        return 1

    except pyodbc.Error as exc:
        print(f"SQL SERVER ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
