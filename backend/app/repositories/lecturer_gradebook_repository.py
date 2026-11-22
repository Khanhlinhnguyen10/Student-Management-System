
"""Lecturer Gradebook data access.

Uses existing SQL tables and stored procedures.
"""

from app.repositories.transaction import connection_scope


SECTION_SQL = """
SELECT
    cs.classSectionId, cs.classCode,
    c.courseCode, c.courseName,
    c.midtermWeight, c.assignmentWeight,
    c.attendanceWeight, c.finalExamWeight
FROM dbo.ClassSections AS cs
JOIN dbo.Lecturers AS l
    ON l.lecturerId = cs.lecturerId
JOIN dbo.Courses AS c
    ON c.courseId = cs.courseId
WHERE cs.classSectionId = ?
  AND l.userId = ?
"""

STUDENTS_SQL = """
SELECT
    e.enrollmentId,
    s.studentId, u.fullName,
    gb.gradebookId,
    gb.midtermMark, gb.assignmentMark,
    gb.attendanceMark, gb.finalExamMark,
    gb.finalScore, gb.letterGrade, gb.isFinalized
FROM dbo.Enrollments AS e
JOIN dbo.Students AS s
    ON s.studentId = e.studentId
JOIN dbo.Users AS u
    ON u.userId = s.userId
LEFT JOIN dbo.GradeBooks AS gb
    ON gb.enrollmentId = e.enrollmentId
WHERE e.classSectionId = ?
ORDER BY s.studentId
"""

ACCESS_SQL = """
SELECT gb.gradebookId, gb.isFinalized
FROM dbo.Enrollments AS e WITH (UPDLOCK, HOLDLOCK)
JOIN dbo.ClassSections AS cs
    ON cs.classSectionId = e.classSectionId
JOIN dbo.Lecturers AS l
    ON l.lecturerId = cs.lecturerId
LEFT JOIN dbo.GradeBooks AS gb WITH (UPDLOCK, HOLDLOCK)
    ON gb.enrollmentId = e.enrollmentId
WHERE e.enrollmentId = ?
  AND e.classSectionId = ?
  AND l.userId = ?
"""

SESSION_SQL = """
SELECT l.lecturerId
FROM dbo.UserSessions AS sess WITH (UPDLOCK, HOLDLOCK)
JOIN dbo.Users AS u
    ON u.userId = sess.userId
JOIN dbo.Lecturers AS l
    ON l.userId = u.userId
WHERE sess.tokenHash = ?
  AND sess.userId = ?
  AND sess.revokedAt IS NULL
  AND sess.expiresAt > SYSUTCDATETIME()
  AND u.isLocked = 0
  AND NOT EXISTS (
      SELECT 1 FROM dbo.Administrators AS a
      WHERE a.userId = u.userId
  )
  AND NOT EXISTS (
      SELECT 1 FROM dbo.Students AS s
      WHERE s.userId = u.userId
  )
"""

NEXT_ID_SQL = """
SELECT MAX(
    TRY_CONVERT(INT, SUBSTRING(gradebookId, 4, 7))
)
FROM dbo.GradeBooks WITH (TABLOCKX, HOLDLOCK)
WHERE gradebookId LIKE
    'GRB[0-9][0-9][0-9][0-9][0-9][0-9][0-9]'
"""

INSERT_SQL = """
INSERT INTO dbo.GradeBooks (
    gradebookId, enrollmentId,
    midtermMark, assignmentMark,
    attendanceMark, finalExamMark,
    finalScore, letterGrade, isFinalized
)
VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, 0)
"""

UPDATE_DRAFT_SQL = """
UPDATE dbo.GradeBooks
SET midtermMark = ?,
    assignmentMark = ?,
    attendanceMark = ?,
    finalExamMark = ?,
    finalScore = NULL,
    letterGrade = NULL,
    isFinalized = 0
WHERE gradebookId = ?
  AND ISNULL(isFinalized, 0) = 0
"""

UPDATE_FINAL_SQL = """
UPDATE dbo.GradeBooks
SET midtermMark = ?,
    assignmentMark = ?,
    attendanceMark = ?,
    finalExamMark = ?
WHERE gradebookId = ?
  AND enrollmentId = ?
  AND ISNULL(isFinalized, 0) = 0
"""

RESULT_SQL = """
SELECT
    gradebookId, enrollmentId,
    midtermMark, assignmentMark,
    attendanceMark, finalExamMark,
    finalScore, letterGrade, isFinalized
FROM dbo.GradeBooks
WHERE enrollmentId = ?
"""

MARK_FIELDS = (
    "midtermMark",
    "assignmentMark",
    "attendanceMark",
    "finalExamMark",
)


def number_or_none(value):
    return None if value is None else float(value)


class LecturerGradebookRepository:
    def __init__(self, connection_factory=None):
        self._connection_factory = connection_factory

    @staticmethod
    def _next_id(cursor):
        cursor.execute(NEXT_ID_SQL)
        number = (cursor.fetchone()[0] or 0) + 1

        if number > 9999999:
            raise RuntimeError("Gradebook ID range exhausted.")

        return f"GRB{number:07d}"

    @staticmethod
    def _lock_enrollment(
        cursor, user_id, section_id, enrollment_id
    ):
        cursor.execute(
            ACCESS_SQL,
            enrollment_id,
            section_id,
            user_id,
        )
        row = cursor.fetchone()

        if row is None:
            raise LookupError(
                "Enrollment not found in assigned class."
            )

        return row[0], bool(row[1])

    @staticmethod
    def _mark_values(marks):
        return tuple(marks[field] for field in MARK_FIELDS)

    def get_section_gradebook(self, user_id, section_id):
        with connection_scope(
            connection_factory=self._connection_factory
        ) as conn:
            cursor = conn.cursor()

            try:
                cursor.execute(
                    SECTION_SQL, section_id, user_id
                )
                section_row = cursor.fetchone()

                if section_row is None:
                    return None

                section = {
                    "classSectionId": section_row[0],
                    "classCode": section_row[1],
                    "courseCode": section_row[2],
                    "courseName": section_row[3],
                    "weights": {
                        "midterm": number_or_none(section_row[4]),
                        "assignment": number_or_none(section_row[5]),
                        "attendance": number_or_none(section_row[6]),
                        "finalExam": number_or_none(section_row[7]),
                    },
                }

                cursor.execute(STUDENTS_SQL, section_id)
                students = []

                for row in cursor.fetchall():
                    students.append({
                        "enrollmentId": row[0],
                        "studentId": row[1],
                        "studentName": row[2],
                        "gradebookId": row[3],
                        "midtermMark": number_or_none(row[4]),
                        "assignmentMark": number_or_none(row[5]),
                        "attendanceMark": number_or_none(row[6]),
                        "finalExamMark": number_or_none(row[7]),
                        "finalScore": number_or_none(row[8]),
                        "letterGrade": row[9],
                        "isFinalized": bool(row[10]),
                    })

                return {
                    "section": section,
                    "students": students,
                }

            finally:
                cursor.close()

    def save_draft(
        self, user_id, section_id, enrollment_id, marks
    ):
        """Save incomplete marks; finalized rows are protected."""

        values = self._mark_values(marks)

        with connection_scope(
            write=True,
            connection_factory=self._connection_factory,
        ) as conn:
            cursor = conn.cursor()

            try:
                gradebook_id, finalized = self._lock_enrollment(
                    cursor, user_id, section_id, enrollment_id
                )

                if finalized:
                    raise PermissionError(
                        "Cannot save a draft over finalized grades."
                    )

                if gradebook_id is None:
                    gradebook_id = self._next_id(cursor)
                    cursor.execute(
                        INSERT_SQL,
                        gradebook_id,
                        enrollment_id,
                        *values,
                    )
                else:
                    cursor.execute(
                        UPDATE_DRAFT_SQL,
                        *values,
                        gradebook_id,
                    )

                    if cursor.rowcount != 1:
                        raise RuntimeError(
                            "Draft changed during save."
                        )

                cursor.execute(RESULT_SQL, enrollment_id)
                row = cursor.fetchone()

                if row is None or bool(row[8]):
                    raise RuntimeError(
                        "Draft save was not confirmed."
                    )

                result = {
                    "gradebookId": row[0],
                    "enrollmentId": row[1],
                    "midtermMark": number_or_none(row[2]),
                    "assignmentMark": number_or_none(row[3]),
                    "attendanceMark": number_or_none(row[4]),
                    "finalExamMark": number_or_none(row[5]),
                    "finalScore": number_or_none(row[6]),
                    "letterGrade": row[7],
                    "isFinalized": False,
                }

            finally:
                cursor.close()

        return result

    def save_final(
        self,
        user_id,
        token_hash,
        section_id,
        enrollment_id,
        marks,
    ):
        """Finalize a draft and recalculate results in one transaction."""

        values = self._mark_values(marks)

        with connection_scope(
            write=True,
            connection_factory=self._connection_factory,
        ) as conn:
            cursor = conn.cursor()

            try:
                # Validate and lock the active lecturer session.
                cursor.execute(
                    SESSION_SQL, token_hash, user_id
                )

                if cursor.fetchone() is None:
                    raise PermissionError(
                        "Active Lecturer session required."
                    )

                # Verify lecturer assignment and lock the gradebook.
                gradebook_id, finalized = self._lock_enrollment(
                    cursor, user_id, section_id, enrollment_id
                )

                # Finalized grades cannot be changed through this API.
                if finalized:
                    raise PermissionError(
                        "Cannot modify finalized grades."
                    )

                if gradebook_id is None:
                    gradebook_id = self._next_id(cursor)

                    cursor.execute(
                        INSERT_SQL,
                        gradebook_id,
                        enrollment_id,
                        *values,
                    )
                else:
                    # Update only a draft gradebook.
                    # The stored procedure calculates the grade and GPA.
                    cursor.execute(
                        UPDATE_FINAL_SQL,
                        *values,
                        gradebook_id,
                        enrollment_id,
                    )

                    if cursor.rowcount != 1:
                        raise RuntimeError(
                            "Gradebook changed during save."
                        )

                cursor.execute(
                    "EXEC dbo.usp_FinalizeGradeBook "
                    "@GradebookId = ?, @TokenHash = ?",
                    gradebook_id,
                    token_hash,
                )

                while cursor.description is None:
                    if not cursor.nextset():
                        raise RuntimeError(
                            "Finalization returned no result."
                        )

                row = cursor.fetchone()

                if (
                    row is None
                    or row[0] != gradebook_id
                    or not bool(row[3])
                ):
                    raise RuntimeError(
                        "Finalization was not confirmed."
                    )

                result = {
                    "gradebookId": row[0],
                    "finalScore": float(row[1]),
                    "letterGrade": row[2],
                    "isFinalized": True,
                }

            finally:
                cursor.close()

        return result
