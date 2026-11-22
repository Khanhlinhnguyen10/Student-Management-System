
"""Business logic for Group 05 View Curriculum use case."""

from app.repositories.student_curriculum_repository import (
    StudentCurriculumRepository,
)


class StudentCurriculumNotFoundError(LookupError):
    """Student or curriculum does not exist."""


class StudentCurriculumAmbiguousError(RuntimeError):
    """Multiple curricula exist without a selection rule."""


class StudentCurriculumService:
    def __init__(
        self,
        repository: StudentCurriculumRepository | None = None,
    ):
        self._repo = (
            repository
            if repository is not None
            else StudentCurriculumRepository()
        )

    def view_curriculum(self, user_id: str) -> dict:
        if (
            not isinstance(user_id, str)
            or not user_id.strip()
            or len(user_id.strip()) > 12
        ):
            raise ValueError("Invalid authenticated user ID.")

        source = self._repo.load_curriculum(
            user_id.strip()
        )

        if source is None:
            raise StudentCurriculumNotFoundError(
                "Student record not found."
            )

        curricula = source["curricula"]

        if not curricula:
            raise StudentCurriculumNotFoundError(
                "No curriculum found for this major."
            )

        if len(curricula) > 1:
            raise StudentCurriculumAmbiguousError(
                "Multiple curricula exist for this major. "
                "An approved curriculum selection rule is required."
            )

        selected = curricula[0]
        curriculum_id = selected["curriculumId"]

        passed_course_ids = source["passedCourseIds"]
        courses_by_id = {}

        # Combine duplicated SQL rows caused by prerequisites.
        for row in source["courseRows"]:
            if row["curriculumId"] != curriculum_id:
                continue

            course_id = row["courseId"]

            if course_id not in courses_by_id:
                courses_by_id[course_id] = {
                    "courseId": course_id,
                    "courseCode": row["courseCode"],
                    "courseName": row["courseName"],
                    "credits": int(row["credits"]),
                    "courseType": row["courseType"],
                    "prerequisites": [],
                    "status": (
                        "Completed"
                        if course_id in passed_course_ids
                        else "Not Completed"
                    ),
                }

            prerequisite_id = row["prerequisiteId"]

            if prerequisite_id is None:
                continue

            prerequisite = {
                "courseId": prerequisite_id,
                "courseCode": row["prerequisiteCode"],
                "courseName": row["prerequisiteName"],
            }

            existing = courses_by_id[course_id][
                "prerequisites"
            ]

            if not any(
                item["courseId"] == prerequisite_id
                for item in existing
            ):
                existing.append(prerequisite)

        courses = sorted(
            courses_by_id.values(),
            key=lambda item: item["courseCode"],
        )

        return {
            "curriculumId": curriculum_id,
            "curriculumName": selected["curriculumName"],
            "academicYear": selected["academicYear"],
            "majorId": source["majorId"],
            "majorName": source["majorName"],
            "courses": courses,
        }
