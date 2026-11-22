
"""Business logic for Student Academic Transcript.

Group 05 - Use Case: View Academic Transcript.

Responsibilities:
- Retrieve the authenticated student's transcript.
- Organize finalized grades by semester.
- Serialize SQL Decimal values for JSON.
- Use stored GPA values without recalculating them.
"""

from decimal import Decimal

from app.repositories.student_transcript_repository import (
    StudentTranscriptRepository,
)


class StudentTranscriptNotFoundError(LookupError):
    """The authenticated student record does not exist."""


class StudentTranscriptService:
    def __init__(
        self,
        repository: StudentTranscriptRepository | None = None,
    ):
        self._repo = (
            repository
            if repository is not None
            else StudentTranscriptRepository()
        )

    @staticmethod
    def _validate_user_id(user_id: str) -> str:
        if (
            not isinstance(user_id, str)
            or not user_id.strip()
            or len(user_id.strip()) > 12
        ):
            raise ValueError("Invalid authenticated user ID.")

        return user_id.strip()

    @staticmethod
    def _number(value):
        """Convert SQL Decimal to a JSON-compatible number."""
        if value is None:
            return None

        if isinstance(value, Decimal):
            return float(value)

        return value

    def view_transcript(self, user_id: str) -> dict:
        user_id = self._validate_user_id(user_id)

        source = self._repo.get_transcript(user_id)

        if source is None:
            raise StudentTranscriptNotFoundError(
                "Student record not found."
            )

        grades = source["grades"]
        semester_results = source["semesterResults"]

        # Match stored GPA results to their semesters.
        gpa_by_semester = {
            result["semesterId"]: result
            for result in semester_results
        }

        semesters_by_id = {}

        # Repository returns finalized GradeBooks only.
        for grade in grades:
            semester_id = grade["semesterId"]

            if semester_id not in semesters_by_id:
                gpa_result = gpa_by_semester.get(
                    semester_id,
                    {},
                )

                semesters_by_id[semester_id] = {
                    "semesterId": semester_id,
                    "semesterName": grade["semesterName"],
                    "academicYear": grade["academicYear"],
                    "semesterGPA": self._number(
                        gpa_result.get("semesterGPA")
                    ),
                    "cumulativeGPA": self._number(
                        gpa_result.get("cumulativeGPA")
                    ),
                    "courses": [],
                }

            semesters_by_id[semester_id]["courses"].append(
                {
                    "courseId": grade["courseId"],
                    "courseCode": grade["courseCode"],
                    "courseName": grade["courseName"],
                    "classCode": grade["classCode"],
                    "credits": int(grade["credits"]),
                    "midtermMark": self._number(
                        grade["midtermMark"]
                    ),
                    "assignmentMark": self._number(
                        grade["assignmentMark"]
                    ),
                    "attendanceMark": self._number(
                        grade["attendanceMark"]
                    ),
                    "finalExamMark": self._number(
                        grade["finalExamMark"]
                    ),
                    "finalScore": self._number(
                        grade["finalScore"]
                    ),
                    "letterGrade": grade["letterGrade"],
                    "gradePoint": self._number(
                        grade["gradePoint"]
                    ),
                }
            )

        semesters = list(semesters_by_id.values())

        # Use the latest stored cumulative GPA.
        # Do not invent or recompute missing GPA values.
        latest_cumulative_gpa = None

        for semester in semesters:
            if semester["cumulativeGPA"] is not None:
                latest_cumulative_gpa = semester[
                    "cumulativeGPA"
                ]

        return {
            "studentId": source["studentId"],
            "hasFinalizedGrades": bool(grades),
            "totalFinalizedResults": len(grades),
            "latestCumulativeGPA": latest_cumulative_gpa,
            "semesters": semesters,
        }
