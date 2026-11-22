
from dataclasses import dataclass


@dataclass(kw_only=True)
class Curriculum:
    """Curriculum record mapped to the official Curriculum table."""

    curriculumId: str
    majorId: str
    curriculumName: str
    academicYear: str
