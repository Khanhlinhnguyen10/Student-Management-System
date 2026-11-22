
from dataclasses import dataclass
from decimal import Decimal


@dataclass(kw_only=True)
class Course:
    """
    Course model - Student Management System Group 05.

    Attributes follow the updated official Data Model.
    """

    courseId: str
    facultyId: str

    courseCode: str
    courseName: str
    credits: int

    midtermWeight: Decimal
    assignmentWeight: Decimal
    attendanceWeight: Decimal
    finalExamWeight: Decimal
