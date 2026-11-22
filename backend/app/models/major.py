
from dataclasses import dataclass


@dataclass(kw_only=True)
class Major:
    """
    Major model - Student Management System Group 05.

    Attributes follow the updated official Data Model.
    """

    majorId: str
    facultyId: str
    majorName: str
    majorCode: str
