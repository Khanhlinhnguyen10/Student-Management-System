
"""Read-only Student Academic Transcript Repository.

Uses the existing SQL Server Data Model.
Only finalized GradeBooks are returned to students.
"""

from typing import Any, Callable

from app.repositories.transaction import connection_scope


_STUDENT_SQL = """
SELECT s.studentId
FROM dbo.Students AS s
WHERE s.userId = ?
"""


_GRADES_SQL = """
SELECT
    sem.semesterId,
    sem.semesterName,
    sem.academicYear,
    cs.classCode,
    c.courseId,
    c.courseCode,
    c.courseName,
    c.credits,
    gb.midtermMark,
    gb.assignmentMark,
    gb.attendanceMark,
    gb.finalExamMark,
    gb.finalScore,
    gb.letterGrade,
    gs.gradePoint
FROM dbo.GradeBooks AS gb
INNER JOIN dbo.Enrollments AS e
    ON e.enrollmentId = gb.enrollmentId
INNER JOIN dbo.ClassSections AS cs
    ON cs.classSectionId = e.classSectionId
INNER JOIN dbo.Courses AS c
    ON c.courseId = cs.courseId
INNER JOIN dbo.Semesters AS sem
    ON sem.semesterId = cs.semesterId
LEFT JOIN dbo.GradeScales AS gs
    ON gs.letterGrade = gb.letterGrade
WHERE e.studentId = ?
  AND gb.isFinalized = 1
ORDER BY
    sem.startDate,
    c.courseCode,
    cs.classCode
"""


_GPA_SQL = """
SELECT
    sem.semesterId,
    sem.semesterName,
    sem.academicYear,
    sr.semesterGPA,
    sr.cumulativeGPA
FROM dbo.SemesterResults AS sr
INNER JOIN dbo.Semesters AS sem
    ON sem.semesterId = sr.semesterId
WHERE sr.studentId = ?
  AND EXISTS (
      SELECT 1
      FROM dbo.Enrollments AS e
      INNER JOIN dbo.ClassSections AS cs
          ON cs.classSectionId = e.classSectionId
      INNER JOIN dbo.GradeBooks AS gb
          ON gb.enrollmentId = e.enrollmentId
      WHERE e.studentId = sr.studentId
        AND cs.semesterId = sr.semesterId
        AND gb.isFinalized = 1
  )
ORDER BY sem.startDate
"""


_GRADE_FIELDS = (
    "semesterId",
    "semesterName",
    "academicYear",
    "classCode",
    "courseId",
    "courseCode",
    "courseName",
    "credits",
    "midtermMark",
    "assignmentMark",
    "attendanceMark",
    "finalExamMark",
    "finalScore",
    "letterGrade",
    "gradePoint",
)


_GPA_FIELDS = (
    "semesterId",
    "semesterName",
    "academicYear",
    "semesterGPA",
    "cumulativeGPA",
)


class StudentTranscriptRepository:
    def __init__(
        self,
        connection_factory: Callable[[], Any] | None = None,
    ):
        self._connection_factory = connection_factory

    @staticmethod
    def _rows_to_dicts(rows, fields):
        return [
            dict(zip(fields, tuple(row)))
            for row in rows
        ]

    def get_transcript(
        self,
        user_id: str,
    ) -> dict | None:

        with connection_scope(
            connection_factory=self._connection_factory
        ) as conn:

            cursor = conn.cursor()

            try:
                # Identify student from authenticated session.
                cursor.execute(
                    _STUDENT_SQL,
                    user_id,
                )

                student_row = cursor.fetchone()

                if student_row is None:
                    return None

                student_id = student_row[0]

                # Read finalized grades only.
                cursor.execute(
                    _GRADES_SQL,
                    student_id,
                )

                grades = self._rows_to_dicts(
                    cursor.fetchall(),
                    _GRADE_FIELDS,
                )

                # Read stored Semester GPA / Cumulative GPA.
                cursor.execute(
                    _GPA_SQL,
                    student_id,
                )

                semester_results = self._rows_to_dicts(
                    cursor.fetchall(),
                    _GPA_FIELDS,
                )

                return {
                    "studentId": student_id,
                    "grades": grades,
                    "semesterResults": semester_results,
                }

            finally:
                cursor.close()
