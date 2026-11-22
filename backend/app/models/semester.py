
from dataclasses import dataclass
from datetime import date


@dataclass(kw_only=True)
class Semester:
    """
    Semester model - Student Management System Group 05.

    Attributes follow the updated official Data Model.

    Note:
    The old Class Diagram contains additional dates
    that are not present in the updated Data Model.
    """

    semesterId: str
    semesterName: str

    endDate: date
    startDate: date

    academicYear: str
