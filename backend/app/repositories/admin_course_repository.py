
"""SQL Server repository for Administrator Course Management."""

from app.repositories.transaction import connection_scope


class CourseNotFoundError(Exception):
    """Course does not exist."""


class CourseConflictError(Exception):
    """Duplicate, dependency or prerequisite conflict."""


COURSE_COLUMNS = """
    c.courseId,
    c.facultyId,
    c.courseCode,
    c.courseName,
    c.credits,
    c.midtermWeight,
    c.assignmentWeight,
    c.attendanceWeight,
    c.finalExamWeight,
    f.facultyCode,
    f.facultyName,
    (
        SELECT COUNT(*)
        FROM dbo.ClassSections AS cs
        WHERE cs.courseId = c.courseId
    ) AS classSectionCount,
    (
        SELECT COUNT(*)
        FROM dbo.CurriculumCourses AS cc
        WHERE cc.courseId = c.courseId
    ) AS curriculumCount,
    (
        SELECT COUNT(*)
        FROM dbo.CoursePrerequisites AS cp
        WHERE cp.prerequisiteId = c.courseId
          AND cp.courseId <> c.courseId
    ) AS dependentCourseCount
"""

COURSE_FROM = """
FROM dbo.Courses AS c
JOIN dbo.Faculties AS f
    ON f.facultyId = c.facultyId
"""

LIST_SQL = f"""
SELECT {COURSE_COLUMNS}
{COURSE_FROM}
ORDER BY c.courseCode;
"""

GET_SQL = f"""
SELECT {COURSE_COLUMNS}
{COURSE_FROM}
WHERE c.courseId = ?;
"""

ALL_PREREQUISITES_SQL = """
SELECT
    cp.courseId,
    cp.prerequisiteId,
    p.courseCode,
    p.courseName
FROM dbo.CoursePrerequisites AS cp
JOIN dbo.Courses AS p
    ON p.courseId = cp.prerequisiteId
ORDER BY cp.courseId, p.courseCode;
"""

ONE_PREREQUISITES_SQL = """
SELECT
    cp.courseId,
    cp.prerequisiteId,
    p.courseCode,
    p.courseName
FROM dbo.CoursePrerequisites AS cp
JOIN dbo.Courses AS p
    ON p.courseId = cp.prerequisiteId
WHERE cp.courseId = ?
ORDER BY p.courseCode;
"""

LOCK_COURSE_SQL = """
SELECT courseId
FROM dbo.Courses WITH (UPDLOCK, HOLDLOCK)
WHERE courseId = ?;
"""

UNIQUE_CODE_SQL = """
SELECT courseId
FROM dbo.Courses WITH (UPDLOCK, HOLDLOCK)
WHERE courseCode = ?;
"""

FACULTY_EXISTS_SQL = """
SELECT facultyId
FROM dbo.Faculties WITH (HOLDLOCK)
WHERE facultyId = ?;
"""

NEXT_ID_SQL = """
SELECT COALESCE(
    MAX(TRY_CONVERT(INT, SUBSTRING(courseId, 4, 7))),
    0
)
FROM dbo.Courses WITH (TABLOCKX, HOLDLOCK)
WHERE courseId LIKE
    'CRS[0-9][0-9][0-9][0-9][0-9][0-9][0-9]';
"""

GRAPH_LOCK_SQL = """
SELECT courseId, prerequisiteId
FROM dbo.CoursePrerequisites WITH (TABLOCKX, HOLDLOCK);
"""

DEPENDENCIES_SQL = """
SELECT
    (
        SELECT COUNT(*)
        FROM dbo.ClassSections WITH (UPDLOCK, HOLDLOCK)
        WHERE courseId = ?
    ),
    (
        SELECT COUNT(*)
        FROM dbo.CurriculumCourses WITH (UPDLOCK, HOLDLOCK)
        WHERE courseId = ?
    ),
    (
        SELECT COUNT(*)
        FROM dbo.CoursePrerequisites WITH (UPDLOCK, HOLDLOCK)
        WHERE prerequisiteId = ?
          AND courseId <> ?
    );
"""


def _course_dict(row):
    return {
        "courseId": row[0],
        "facultyId": row[1],
        "courseCode": row[2],
        "courseName": row[3],
        "credits": int(row[4]),
        "midtermWeight": float(row[5]),
        "assignmentWeight": float(row[6]),
        "attendanceWeight": float(row[7]),
        "finalExamWeight": float(row[8]),
        "facultyCode": row[9],
        "facultyName": row[10],
        "classSectionCount": int(row[11]),
        "curriculumCount": int(row[12]),
        "dependentCourseCount": int(row[13]),
        "prerequisiteIds": [],
        "prerequisites": [],
    }


def _attach_prerequisite(record, row):
    record["prerequisiteIds"].append(row[1])
    record["prerequisites"].append({
        "courseId": row[1],
        "courseCode": row[2],
        "courseName": row[3],
    })


def _is_duplicate_error(exc):
    return (
        "2627" in str(exc)
        or "2601" in str(exc)
    )


def _is_foreign_key_error(exc):
    return "547" in str(exc)


class AdminCourseRepository:
    def __init__(self, connection_factory=None):
        self._connection_factory = connection_factory

    # =========================================
    # READ - LIST
    # =========================================

    def list_courses(self):
        with connection_scope(
            connection_factory=self._connection_factory
        ) as conn:
            cursor = conn.cursor()

            try:
                cursor.execute(LIST_SQL)

                records = [
                    _course_dict(row)
                    for row in cursor.fetchall()
                ]

                mapping = {
                    item["courseId"]: item
                    for item in records
                }

                cursor.execute(ALL_PREREQUISITES_SQL)

                for row in cursor.fetchall():
                    record = mapping.get(row[0])

                    if record is not None:
                        _attach_prerequisite(record, row)

                return records

            finally:
                cursor.close()

    # =========================================
    # READ - DETAILS
    # =========================================

    def get_course(self, course_id):
        with connection_scope(
            connection_factory=self._connection_factory
        ) as conn:
            cursor = conn.cursor()

            try:
                cursor.execute(GET_SQL, course_id)
                row = cursor.fetchone()

                if row is None:
                    return None

                record = _course_dict(row)

                cursor.execute(
                    ONE_PREREQUISITES_SQL,
                    course_id,
                )

                for item in cursor.fetchall():
                    _attach_prerequisite(record, item)

                return record

            finally:
                cursor.close()

    # =========================================
    # INTERNAL - EXISTING COURSE
    # =========================================

    @staticmethod
    def _ensure_course(cursor, course_id):
        cursor.execute(
            LOCK_COURSE_SQL,
            course_id,
        )

        if cursor.fetchone() is None:
            raise CourseNotFoundError(
                "Course not found."
            )

    # =========================================
    # INTERNAL - UNIQUE COURSE CODE
    # =========================================

    @staticmethod
    def _ensure_unique_code(cursor, code):
        cursor.execute(
            UNIQUE_CODE_SQL,
            code,
        )

        if cursor.fetchone() is not None:
            raise CourseConflictError(
                "Course Code already exists."
            )

    # =========================================
    # INTERNAL - FACULTY EXISTS
    # =========================================

    @staticmethod
    def _ensure_faculty(cursor, faculty_id):
        cursor.execute(
            FACULTY_EXISTS_SQL,
            faculty_id,
        )

        if cursor.fetchone() is None:
            raise CourseConflictError(
                "Managing Faculty does not exist."
            )

    # =========================================
    # INTERNAL - PREREQUISITES EXIST
    # =========================================

    @staticmethod
    def _ensure_prerequisites(cursor, ids):
        if not ids:
            return

        placeholders = ", ".join(
            "?" for _ in ids
        )

        cursor.execute(
            "SELECT courseId "
            "FROM dbo.Courses WITH (HOLDLOCK) "
            f"WHERE courseId IN ({placeholders});",
            *ids,
        )

        found = {
            row[0]
            for row in cursor.fetchall()
        }

        if found != set(ids):
            raise CourseConflictError(
                "One or more prerequisite courses "
                "do not exist."
            )

    # =========================================
    # INTERNAL - DETECT PREREQUISITE CYCLES
    # =========================================

    @staticmethod
    def _check_cycle(cursor, course_id, ids):
        # Lock the prerequisite table during graph
        # validation and modification.
        cursor.execute(GRAPH_LOCK_SQL)

        graph = {}

        for row in cursor.fetchall():
            graph.setdefault(
                row[0],
                set(),
            ).add(row[1])

        # Simulate replacing the selected course's
        # prerequisite edges before writing.
        graph[course_id] = set(ids)

        for prerequisite_id in ids:
            stack = [prerequisite_id]
            visited = set()

            while stack:
                current = stack.pop()

                if current == course_id:
                    raise CourseConflictError(
                        "Circular prerequisite dependency "
                        "is not allowed."
                    )

                if current in visited:
                    continue

                visited.add(current)

                stack.extend(
                    graph.get(current, ())
                )

    # =========================================
    # INTERNAL - WRITE PREREQUISITES
    # =========================================

    @staticmethod
    def _replace_prerequisites(
        cursor,
        course_id,
        ids,
    ):
        cursor.execute(
            """
            DELETE FROM dbo.CoursePrerequisites
            WHERE courseId = ?;
            """,
            course_id,
        )

        for prerequisite_id in ids:
            cursor.execute(
                """
                INSERT INTO dbo.CoursePrerequisites (
                    courseId,
                    prerequisiteId
                )
                VALUES (?, ?);
                """,
                course_id,
                prerequisite_id,
            )

    # =========================================
    # CREATE COURSE
    # =========================================

    def create_course(self, fields):
        with connection_scope(
            write=True,
            connection_factory=self._connection_factory,
        ) as conn:
            cursor = conn.cursor()

            try:
                cursor.execute(NEXT_ID_SQL)

                number = int(
                    cursor.fetchone()[0]
                ) + 1

                if number > 9999999:
                    raise RuntimeError(
                        "Course ID range exhausted."
                    )

                course_id = f"CRS{number:07d}"

                self._ensure_unique_code(
                    cursor,
                    fields["courseCode"],
                )

                self._ensure_faculty(
                    cursor,
                    fields["facultyId"],
                )

                ids = fields["prerequisiteIds"]

                self._ensure_prerequisites(
                    cursor,
                    ids,
                )

                self._check_cycle(
                    cursor,
                    course_id,
                    ids,
                )

                try:
                    cursor.execute(
                        """
                        INSERT INTO dbo.Courses (
                            courseId,
                            facultyId,
                            courseCode,
                            courseName,
                            credits,
                            midtermWeight,
                            assignmentWeight,
                            attendanceWeight,
                            finalExamWeight
                        )
                        OUTPUT INSERTED.courseId
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                        """,
                        course_id,
                        fields["facultyId"],
                        fields["courseCode"],
                        fields["courseName"],
                        fields["credits"],
                        fields["midtermWeight"],
                        fields["assignmentWeight"],
                        fields["attendanceWeight"],
                        fields["finalExamWeight"],
                    )

                    saved = cursor.fetchone()

                    if saved is None or saved[0] != course_id:
                        raise RuntimeError(
                            "Course creation not confirmed."
                        )

                    self._replace_prerequisites(
                        cursor,
                        course_id,
                        ids,
                    )

                except Exception as exc:
                    if _is_duplicate_error(exc):
                        raise CourseConflictError(
                            "Course Code already exists "
                            "or prerequisite is duplicated."
                        ) from exc

                    if _is_foreign_key_error(exc):
                        raise CourseConflictError(
                            "Faculty or prerequisite "
                            "is no longer available."
                        ) from exc

                    raise

                return course_id

            finally:
                cursor.close()

    # =========================================
    # UPDATE COURSE
    # =========================================

    def update_course(self, course_id, fields):
        with connection_scope(
            write=True,
            connection_factory=self._connection_factory,
        ) as conn:
            cursor = conn.cursor()

            try:
                self._ensure_course(
                    cursor,
                    course_id,
                )

                self._ensure_faculty(
                    cursor,
                    fields["facultyId"],
                )

                ids = fields["prerequisiteIds"]

                self._ensure_prerequisites(
                    cursor,
                    ids,
                )

                self._check_cycle(
                    cursor,
                    course_id,
                    ids,
                )

                try:
                    cursor.execute(
                        """
                        UPDATE dbo.Courses
                        SET
                            facultyId = ?,
                            courseName = ?,
                            credits = ?,
                            midtermWeight = ?,
                            assignmentWeight = ?,
                            attendanceWeight = ?,
                            finalExamWeight = ?
                        OUTPUT INSERTED.courseId
                        WHERE courseId = ?;
                        """,
                        fields["facultyId"],
                        fields["courseName"],
                        fields["credits"],
                        fields["midtermWeight"],
                        fields["assignmentWeight"],
                        fields["attendanceWeight"],
                        fields["finalExamWeight"],
                        course_id,
                    )

                    saved = cursor.fetchone()

                    if saved is None or saved[0] != course_id:
                        raise RuntimeError(
                            "Course update not confirmed."
                        )

                    self._replace_prerequisites(
                        cursor,
                        course_id,
                        ids,
                    )

                except Exception as exc:
                    if _is_foreign_key_error(exc):
                        raise CourseConflictError(
                            "Faculty or prerequisite "
                            "is no longer available."
                        ) from exc

                    raise

                return course_id

            finally:
                cursor.close()

    # =========================================
    # DELETE COURSE
    # =========================================

    def delete_course(self, course_id):
        with connection_scope(
            write=True,
            connection_factory=self._connection_factory,
        ) as conn:
            cursor = conn.cursor()

            try:
                self._ensure_course(
                    cursor,
                    course_id,
                )

                # Prevent concurrent prerequisite
                # changes while checking references.
                cursor.execute(GRAPH_LOCK_SQL)
                cursor.fetchall()

                cursor.execute(
                    DEPENDENCIES_SQL,
                    course_id,
                    course_id,
                    course_id,
                    course_id,
                )

                row = cursor.fetchone()

                if row is None:
                    raise RuntimeError(
                        "Unable to verify course dependencies."
                    )

                if any(int(value) > 0 for value in row):
                    raise CourseConflictError(
                        "Cannot delete a course linked to "
                        "class sections, curriculum records "
                        "or dependent courses."
                    )

                try:
                    # Remove this course's own outgoing
                    # prerequisite edges before deleting.
                    cursor.execute(
                        """
                        DELETE FROM dbo.CoursePrerequisites
                        WHERE courseId = ?;
                        """,
                        course_id,
                    )

                    cursor.execute(
                        """
                        DELETE FROM dbo.Courses
                        OUTPUT DELETED.courseId
                        WHERE courseId = ?;
                        """,
                        course_id,
                    )

                    deleted = cursor.fetchone()

                except Exception as exc:
                    if _is_foreign_key_error(exc):
                        raise CourseConflictError(
                            "Cannot delete a course "
                            "linked to academic data."
                        ) from exc

                    raise

                if deleted is None or deleted[0] != course_id:
                    raise RuntimeError(
                        "Course deletion not confirmed."
                    )

                return True

            finally:
                cursor.close()
