
"""SQL Server repository for Administrator Class Section Management.

Use Cases 35-39:
- Manage Class Sections
- Create Class Sections
- View Class Sections
- Update Class Sections
- Delete Class Sections

Lecturer assignment is managed separately by Use Case 40.
"""

from app.repositories.transaction import connection_scope


# ============================================================
# DOMAIN EXCEPTIONS
# ============================================================

class ClassSectionNotFoundError(Exception):
    """The requested class section does not exist."""


class ClassSectionConflictError(Exception):
    """A business rule or data constraint was violated."""


# ============================================================
# SQL - LIST AND DETAILS
# ============================================================

SECTION_COLUMNS = """
    cs.classSectionId,
    cs.classCode,
    cs.courseId,
    c.courseCode,
    c.courseName,
    cs.semesterId,
    s.semesterName,
    cs.lecturerId,
    u.fullName AS lecturerName,
    cs.maxCapacity,
    cs.currentEnrollment,
    cs.room,
    cs.dayOfWeek,
    cs.startTime,
    cs.endTime
"""

SECTION_JOINS = """
FROM dbo.ClassSections AS cs
INNER JOIN dbo.Courses AS c
    ON c.courseId = cs.courseId
INNER JOIN dbo.Semesters AS s
    ON s.semesterId = cs.semesterId
LEFT JOIN dbo.Lecturers AS l
    ON l.lecturerId = cs.lecturerId
LEFT JOIN dbo.Users AS u
    ON u.userId = l.userId
"""

LIST_SQL = f"""
SELECT {SECTION_COLUMNS}
{SECTION_JOINS}
ORDER BY
    s.startDate DESC,
    cs.classCode;
"""

LIST_BY_SEMESTER_SQL = f"""
SELECT {SECTION_COLUMNS}
{SECTION_JOINS}
WHERE cs.semesterId = ?
ORDER BY cs.classCode;
"""

GET_SQL = f"""
SELECT {SECTION_COLUMNS}
{SECTION_JOINS}
WHERE cs.classSectionId = ?;
"""


# ============================================================
# SQL - DROPDOWN DATA
# ============================================================

SEMESTERS_SQL = """
SELECT
    semesterId,
    semesterName,
    academicYear,
    startDate,
    endDate
FROM dbo.Semesters
ORDER BY startDate DESC, semesterId DESC;
"""

COURSES_SQL = """
SELECT
    courseId,
    courseCode,
    courseName,
    facultyId
FROM dbo.Courses
ORDER BY courseCode;
"""


# ============================================================
# SQL - VALIDATION AND LOCKING
# ============================================================

NEXT_ID_SQL = """
SELECT COALESCE(
    MAX(
        TRY_CONVERT(
            INT,
            SUBSTRING(classSectionId, 4, 7)
        )
    ),
    0
)
FROM dbo.ClassSections WITH (TABLOCKX, HOLDLOCK)
WHERE classSectionId LIKE
    'CLS[0-9][0-9][0-9][0-9][0-9][0-9][0-9]';
"""

LOCK_SECTION_SQL = """
SELECT
    classSectionId,
    classCode,
    courseId,
    semesterId,
    lecturerId,
    currentEnrollment
FROM dbo.ClassSections WITH (UPDLOCK, HOLDLOCK)
WHERE classSectionId = ?;
"""

DUPLICATE_CODE_SQL = """
SELECT classSectionId
FROM dbo.ClassSections WITH (UPDLOCK, HOLDLOCK)
WHERE classCode = ?;
"""

COURSE_EXISTS_SQL = """
SELECT courseId
FROM dbo.Courses WITH (HOLDLOCK)
WHERE courseId = ?;
"""

SEMESTER_EXISTS_SQL = """
SELECT semesterId
FROM dbo.Semesters WITH (HOLDLOCK)
WHERE semesterId = ?;
"""


# ============================================================
# SQL - ROOM CONFLICT
# ============================================================

ROOM_CONFLICT_SQL = """
SELECT TOP (1)
    classCode,
    room,
    dayOfWeek,
    startTime,
    endTime
FROM dbo.ClassSections WITH (UPDLOCK, HOLDLOCK)
WHERE semesterId = ?
  AND classSectionId <> ?
  AND room = ?
  AND dayOfWeek = ?
  AND startTime < ?
  AND endTime > ?
ORDER BY classCode;
"""


# ============================================================
# SQL - LECTURER SCHEDULE CONFLICT
# ============================================================

LECTURER_CONFLICT_SQL = """
SELECT TOP (1)
    classCode,
    dayOfWeek,
    startTime,
    endTime
FROM dbo.ClassSections WITH (UPDLOCK, HOLDLOCK)
WHERE semesterId = ?
  AND classSectionId <> ?
  AND lecturerId = ?
  AND dayOfWeek = ?
  AND startTime < ?
  AND endTime > ?
ORDER BY classCode;
"""


# ============================================================
# SQL - ENROLLMENT DEPENDENCIES
# ============================================================

ENROLLMENT_DEPENDENCIES_SQL = """
SELECT COUNT(*)
FROM dbo.Enrollments WITH (UPDLOCK, HOLDLOCK)
WHERE classSectionId = ?;
"""


# ============================================================
# HELPERS
# ============================================================

def _time_text(value):
    """Convert a SQL TIME value to HH:MM."""

    if value is None:
        return None

    if hasattr(value, "strftime"):
        return value.strftime("%H:%M")

    return str(value)[:5]


def _section_dict(row):
    """Convert a database row to a JSON-ready object."""

    return {
        "classSectionId": row[0],
        "classCode": row[1],
        "courseId": row[2],
        "courseCode": row[3],
        "courseName": row[4],
        "semesterId": row[5],
        "semesterName": row[6],
        "lecturerId": row[7],
        "lecturerName": row[8],
        "maxCapacity": int(row[9]),
        "currentEnrollment": int(row[10]),
        "room": row[11],
        "dayOfWeek": (
            int(row[12])
            if row[12] is not None
            else None
        ),
        "startTime": _time_text(row[13]),
        "endTime": _time_text(row[14]),
    }


def _is_duplicate_error(exc):
    message = str(exc)

    return (
        "2627" in message
        or "2601" in message
    )


def _is_foreign_key_error(exc):
    return "547" in str(exc)


# ============================================================
# REPOSITORY
# ============================================================

class AdminClassSectionRepository:
    """Database operations for Administrator Class Sections."""

    def __init__(self, connection_factory=None):
        self._connection_factory = connection_factory

    # ========================================================
    # 1. LIST CLASS SECTIONS
    # ========================================================

    def list_sections(self, semester_id=None):
        """Return all sections or sections of one semester."""

        with connection_scope(
            connection_factory=self._connection_factory
        ) as conn:

            cursor = conn.cursor()

            try:
                if semester_id is None:
                    cursor.execute(LIST_SQL)
                else:
                    cursor.execute(
                        LIST_BY_SEMESTER_SQL,
                        semester_id,
                    )

                return [
                    _section_dict(row)
                    for row in cursor.fetchall()
                ]

            finally:
                cursor.close()

    # ========================================================
    # 2. GET CLASS SECTION DETAILS
    # ========================================================

    def get_section(self, section_id):
        """Return details of one class section."""

        with connection_scope(
            connection_factory=self._connection_factory
        ) as conn:

            cursor = conn.cursor()

            try:
                cursor.execute(
                    GET_SQL,
                    section_id,
                )

                row = cursor.fetchone()

                if row is None:
                    return None

                return _section_dict(row)

            finally:
                cursor.close()

    # ========================================================
    # 3. LIST SEMESTERS FOR DROPDOWN
    # ========================================================

    def list_semesters(self):
        """Return available semesters."""

        with connection_scope(
            connection_factory=self._connection_factory
        ) as conn:

            cursor = conn.cursor()

            try:
                cursor.execute(SEMESTERS_SQL)

                return [
                    {
                        "semesterId": row[0],
                        "semesterName": row[1],
                        "academicYear": row[2],
                        "startDate": row[3].isoformat(),
                        "endDate": row[4].isoformat(),
                    }
                    for row in cursor.fetchall()
                ]

            finally:
                cursor.close()

    # ========================================================
    # 4. LIST COURSES FOR DROPDOWN
    # ========================================================

    def list_courses(self):
        """Return courses for Class Section creation."""

        with connection_scope(
            connection_factory=self._connection_factory
        ) as conn:

            cursor = conn.cursor()

            try:
                cursor.execute(COURSES_SQL)

                return [
                    {
                        "courseId": row[0],
                        "courseCode": row[1],
                        "courseName": row[2],
                        "facultyId": row[3],
                    }
                    for row in cursor.fetchall()
                ]

            finally:
                cursor.close()

    # ========================================================
    # INTERNAL - LOCK EXISTING SECTION
    # ========================================================

    @staticmethod
    def _get_locked_section(cursor, section_id):
        cursor.execute(
            LOCK_SECTION_SQL,
            section_id,
        )

        row = cursor.fetchone()

        if row is None:
            raise ClassSectionNotFoundError(
                "Class Section not found."
            )

        return {
            "classSectionId": row[0],
            "classCode": row[1],
            "courseId": row[2],
            "semesterId": row[3],
            "lecturerId": row[4],
            "currentEnrollment": int(row[5]),
        }

    # ========================================================
    # INTERNAL - CHECK UNIQUE CLASS CODE
    # ========================================================

    @staticmethod
    def _ensure_unique_code(cursor, class_code):
        cursor.execute(
            DUPLICATE_CODE_SQL,
            class_code,
        )

        if cursor.fetchone() is not None:
            raise ClassSectionConflictError(
                "Class Code already exists."
            )

    # ========================================================
    # INTERNAL - VERIFY COURSE
    # ========================================================

    @staticmethod
    def _ensure_course(cursor, course_id):
        cursor.execute(
            COURSE_EXISTS_SQL,
            course_id,
        )

        if cursor.fetchone() is None:
            raise ClassSectionConflictError(
                "Selected Course does not exist."
            )

    # ========================================================
    # INTERNAL - VERIFY SEMESTER
    # ========================================================

    @staticmethod
    def _ensure_semester(cursor, semester_id):
        cursor.execute(
            SEMESTER_EXISTS_SQL,
            semester_id,
        )

        if cursor.fetchone() is None:
            raise ClassSectionConflictError(
                "Selected Semester does not exist."
            )

    # ========================================================
    # INTERNAL - CHECK ROOM SCHEDULE
    # ========================================================

    @staticmethod
    def _check_room_conflict(
        cursor,
        section_id,
        semester_id,
        room,
        day_of_week,
        start_time,
        end_time,
    ):
        """Reject overlapping classes in the same room."""

        if (
            room is None
            or day_of_week is None
            or start_time is None
            or end_time is None
        ):
            return

        cursor.execute(
            ROOM_CONFLICT_SQL,
            semester_id,
            section_id,
            room,
            day_of_week,
            end_time,
            start_time,
        )

        conflict = cursor.fetchone()

        if conflict is None:
            return

        other_code = conflict[0]
        other_room = conflict[1]
        other_day = conflict[2]
        other_start = _time_text(conflict[3])
        other_end = _time_text(conflict[4])

        raise ClassSectionConflictError(
            "Room schedule conflict with "
            f"{other_code}, room {other_room}, "
            f"day {other_day}, "
            f"{other_start}-{other_end}."
        )

    # ========================================================
    # INTERNAL - CHECK LECTURER SCHEDULE
    # ========================================================

    @staticmethod
    def _check_lecturer_conflict(
        cursor,
        section_id,
        semester_id,
        lecturer_id,
        day_of_week,
        start_time,
        end_time,
    ):
        """Protect assigned lecturer from overlapping classes."""

        if (
            lecturer_id is None
            or day_of_week is None
            or start_time is None
            or end_time is None
        ):
            return

        cursor.execute(
            LECTURER_CONFLICT_SQL,
            semester_id,
            section_id,
            lecturer_id,
            day_of_week,
            end_time,
            start_time,
        )

        conflict = cursor.fetchone()

        if conflict is None:
            return

        other_code = conflict[0]
        other_day = conflict[1]
        other_start = _time_text(conflict[2])
        other_end = _time_text(conflict[3])

        raise ClassSectionConflictError(
            "Lecturer schedule conflict with "
            f"{other_code}, day {other_day}, "
            f"{other_start}-{other_end}."
        )

    # ========================================================
    # 5. CREATE CLASS SECTION
    # ========================================================

    def create_section(self, fields):
        """Create a section without assigning a lecturer."""

        with connection_scope(
            write=True,
            connection_factory=self._connection_factory,
        ) as conn:

            cursor = conn.cursor()

            try:
                # Generate Class Section ID while holding
                # an exclusive table lock.
                cursor.execute(NEXT_ID_SQL)

                next_number = (
                    int(cursor.fetchone()[0]) + 1
                )

                if next_number > 9999999:
                    raise RuntimeError(
                        "Class Section ID range exhausted."
                    )

                section_id = (
                    f"CLS{next_number:07d}"
                )

                # Check identification data.
                self._ensure_unique_code(
                    cursor,
                    fields["classCode"],
                )

                self._ensure_course(
                    cursor,
                    fields["courseId"],
                )

                self._ensure_semester(
                    cursor,
                    fields["semesterId"],
                )

                # Validate room availability.
                self._check_room_conflict(
                    cursor,
                    section_id,
                    fields["semesterId"],
                    fields["room"],
                    fields["dayOfWeek"],
                    fields["startTime"],
                    fields["endTime"],
                )

                try:
                    cursor.execute(
                        """
                        INSERT INTO dbo.ClassSections (
                            classSectionId,
                            lecturerId,
                            courseId,
                            semesterId,
                            classCode,
                            maxCapacity,
                            currentEnrollment,
                            room,
                            dayOfWeek,
                            startTime,
                            endTime
                        )
                        OUTPUT INSERTED.classSectionId
                        VALUES (
                            ?,
                            NULL,
                            ?,
                            ?,
                            ?,
                            ?,
                            0,
                            ?,
                            ?,
                            ?,
                            ?
                        );
                        """,
                        section_id,
                        fields["courseId"],
                        fields["semesterId"],
                        fields["classCode"],
                        fields["maxCapacity"],
                        fields["room"],
                        fields["dayOfWeek"],
                        fields["startTime"],
                        fields["endTime"],
                    )

                    saved = cursor.fetchone()

                except Exception as exc:
                    if _is_duplicate_error(exc):
                        raise ClassSectionConflictError(
                            "Class Code already exists."
                        ) from exc

                    if _is_foreign_key_error(exc):
                        raise ClassSectionConflictError(
                            "Selected Course or Semester "
                            "does not exist."
                        ) from exc

                    raise

                if (
                    saved is None
                    or saved[0] != section_id
                ):
                    raise RuntimeError(
                        "Class Section creation not confirmed."
                    )

                return section_id

            finally:
                cursor.close()

    # ========================================================
    # 6. UPDATE CLASS SECTION
    # ========================================================

    def update_section(self, section_id, fields):
        """Update capacity, room and schedule only.

        Class Code, Course, Semester and Lecturer
        remain unchanged.
        """

        with connection_scope(
            write=True,
            connection_factory=self._connection_factory,
        ) as conn:

            cursor = conn.cursor()

            try:
                existing = self._get_locked_section(
                    cursor,
                    section_id,
                )

                # Capacity cannot be lower than
                # the current enrollment.
                if (
                    fields["maxCapacity"]
                    < existing["currentEnrollment"]
                ):
                    raise ClassSectionConflictError(
                        "Maximum Capacity cannot be "
                        "lower than Current Enrollment."
                    )

                # Verify room conflict in the
                # original semester.
                self._check_room_conflict(
                    cursor,
                    section_id,
                    existing["semesterId"],
                    fields["room"],
                    fields["dayOfWeek"],
                    fields["startTime"],
                    fields["endTime"],
                )

                # If lecturer is already assigned,
                # protect that lecturer's schedule.
                self._check_lecturer_conflict(
                    cursor,
                    section_id,
                    existing["semesterId"],
                    existing["lecturerId"],
                    fields["dayOfWeek"],
                    fields["startTime"],
                    fields["endTime"],
                )

                cursor.execute(
                    """
                    UPDATE dbo.ClassSections
                    SET
                        maxCapacity = ?,
                        room = ?,
                        dayOfWeek = ?,
                        startTime = ?,
                        endTime = ?
                    OUTPUT INSERTED.classSectionId
                    WHERE classSectionId = ?;
                    """,
                    fields["maxCapacity"],
                    fields["room"],
                    fields["dayOfWeek"],
                    fields["startTime"],
                    fields["endTime"],
                    section_id,
                )

                saved = cursor.fetchone()

                if (
                    saved is None
                    or saved[0] != section_id
                ):
                    raise RuntimeError(
                        "Class Section update not confirmed."
                    )

                return section_id

            finally:
                cursor.close()

    # ========================================================
    # 7. DELETE CLASS SECTION
    # ========================================================

    def delete_section(self, section_id):
        """Delete only when academic enrollment is absent."""

        with connection_scope(
            write=True,
            connection_factory=self._connection_factory,
        ) as conn:

            cursor = conn.cursor()

            try:
                existing = self._get_locked_section(
                    cursor,
                    section_id,
                )

                # Protect current enrollment.
                if existing["currentEnrollment"] > 0:
                    raise ClassSectionConflictError(
                        "Cannot delete a Class Section "
                        "with enrolled students."
                    )

                # Protect all enrollment records,
                # including historical records.
                cursor.execute(
                    ENROLLMENT_DEPENDENCIES_SQL,
                    section_id,
                )

                enrollment_count = int(
                    cursor.fetchone()[0]
                )

                if enrollment_count > 0:
                    raise ClassSectionConflictError(
                        "Cannot delete a Class Section "
                        "linked to enrollment records."
                    )

                try:
                    cursor.execute(
                        """
                        DELETE FROM dbo.ClassSections
                        OUTPUT DELETED.classSectionId
                        WHERE classSectionId = ?;
                        """,
                        section_id,
                    )

                    deleted = cursor.fetchone()

                except Exception as exc:
                    if _is_foreign_key_error(exc):
                        raise ClassSectionConflictError(
                            "Cannot delete a Class Section "
                            "linked to academic data."
                        ) from exc

                    raise

                if (
                    deleted is None
                    or deleted[0] != section_id
                ):
                    raise RuntimeError(
                        "Class Section deletion not confirmed."
                    )

                return True

            finally:
                cursor.close()
