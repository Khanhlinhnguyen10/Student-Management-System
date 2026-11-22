
"""Repository for lecturer's assigned class sections."""

from app.repositories.transaction import connection_scope


SECTIONS_SQL = """
SELECT
    cs.classSectionId,
    cs.classCode,
    c.courseId,
    c.courseCode,
    c.courseName,
    c.credits,
    sem.semesterId,
    sem.semesterName,
    sem.academicYear,
    COUNT(e.enrollmentId) AS studentCount,
    cs.maxCapacity
FROM dbo.Lecturers AS l
JOIN dbo.ClassSections AS cs
    ON cs.lecturerId = l.lecturerId
JOIN dbo.Courses AS c
    ON c.courseId = cs.courseId
JOIN dbo.Semesters AS sem
    ON sem.semesterId = cs.semesterId
LEFT JOIN dbo.Enrollments AS e
    ON e.classSectionId = cs.classSectionId
WHERE l.userId = ?
GROUP BY
    cs.classSectionId,
    cs.classCode,
    c.courseId,
    c.courseCode,
    c.courseName,
    c.credits,
    sem.semesterId,
    sem.semesterName,
    sem.academicYear,
    sem.startDate,
    cs.maxCapacity
ORDER BY
    sem.startDate DESC,
    c.courseCode,
    cs.classCode
"""


FIELDS = (
    "classSectionId",
    "classCode",
    "courseId",
    "courseCode",
    "courseName",
    "credits",
    "semesterId",
    "semesterName",
    "academicYear",
    "studentCount",
    "maxCapacity",
)


class LecturerSectionsRepository:

    def __init__(self, connection_factory=None):
        self._connection_factory = connection_factory

    def list_assigned_sections(self, user_id):
        with connection_scope(
            connection_factory=self._connection_factory
        ) as conn:
            cursor = conn.cursor()

            try:
                cursor.execute(SECTIONS_SQL, user_id)

                return [
                    dict(zip(FIELDS, tuple(row)))
                    for row in cursor.fetchall()
                ]

            finally:
                cursor.close()
