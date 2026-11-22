
"""Read-only SQL Server access for Student Curriculum.

Uses existing Group 05 tables:
Students, Majors, Curriculum, CurriculumCourses,
Courses, CoursePrerequisites, Enrollments,
ClassSections, GradeBooks and GradeScales.
"""

from typing import Any, Callable

from app.repositories.transaction import connection_scope


_STUDENT_SQL = """
SELECT
    s.studentId,
    s.majorId,
    m.majorName
FROM dbo.Students AS s
INNER JOIN dbo.Majors AS m
    ON m.majorId = s.majorId
WHERE s.userId = ?
"""

_CURRICULUM_SQL = """
SELECT
    curriculumId,
    curriculumName,
    academicYear
FROM dbo.Curriculum
WHERE majorId = ?
ORDER BY academicYear DESC, curriculumId
"""

_COURSES_SQL = """
SELECT
    cc.curriculumId,
    c.courseId,
    c.courseCode,
    c.courseName,
    c.credits,
    cc.courseType,
    p.courseId AS prerequisiteId,
    p.courseCode AS prerequisiteCode,
    p.courseName AS prerequisiteName
FROM dbo.Curriculum AS cu
INNER JOIN dbo.CurriculumCourses AS cc
    ON cc.curriculumId = cu.curriculumId
INNER JOIN dbo.Courses AS c
    ON c.courseId = cc.courseId
LEFT JOIN dbo.CoursePrerequisites AS cp
    ON cp.courseId = c.courseId
LEFT JOIN dbo.Courses AS p
    ON p.courseId = cp.prerequisiteId
WHERE cu.majorId = ?
ORDER BY
    cc.curriculumId,
    c.courseCode,
    p.courseCode
"""

_PASSED_COURSES_SQL = """
SELECT DISTINCT
    cs.courseId
FROM dbo.Enrollments AS e
INNER JOIN dbo.ClassSections AS cs
    ON cs.classSectionId = e.classSectionId
INNER JOIN dbo.GradeBooks AS gb
    ON gb.enrollmentId = e.enrollmentId
INNER JOIN dbo.GradeScales AS gs
    ON gs.letterGrade = gb.letterGrade
   AND gb.finalScore BETWEEN gs.minScore AND gs.maxScore
WHERE e.studentId = ?
  AND gb.isFinalized = 1
  AND gs.isPassing = 1
"""


class StudentCurriculumRepository:
    """Retrieve curriculum source records using one SQL connection."""

    def __init__(
        self,
        connection_factory: Callable[[], Any] | None = None,
    ):
        self._connection_factory = connection_factory

    def load_curriculum(self, user_id: str) -> dict | None:
        with connection_scope(
            connection_factory=self._connection_factory
        ) as conn:
            cursor = conn.cursor()

            try:
                # Identify the student through authenticated userId.
                cursor.execute(_STUDENT_SQL, user_id)
                identity = cursor.fetchone()

                if identity is None:
                    return None

                student_id = identity[0]
                major_id = identity[1]
                major_name = identity[2]

                # Retrieve all curricula assigned to this major.
                cursor.execute(_CURRICULUM_SQL, major_id)

                curricula = [
                    {
                        "curriculumId": row[0],
                        "curriculumName": row[1],
                        "academicYear": row[2],
                    }
                    for row in cursor.fetchall()
                ]

                # Retrieve courses and prerequisites.
                cursor.execute(_COURSES_SQL, major_id)

                course_rows = [
                    {
                        "curriculumId": row[0],
                        "courseId": row[1],
                        "courseCode": row[2],
                        "courseName": row[3],
                        "credits": row[4],
                        "courseType": row[5],
                        "prerequisiteId": row[6],
                        "prerequisiteCode": row[7],
                        "prerequisiteName": row[8],
                    }
                    for row in cursor.fetchall()
                ]

                # Retrieve only finalized passing course attempts.
                cursor.execute(
                    _PASSED_COURSES_SQL,
                    student_id,
                )

                passed_course_ids = {
                    row[0]
                    for row in cursor.fetchall()
                }

                return {
                    "studentId": student_id,
                    "majorId": major_id,
                    "majorName": major_name,
                    "curricula": curricula,
                    "courseRows": course_rows,
                    "passedCourseIds": passed_course_ids,
                }

            finally:
                cursor.close()
