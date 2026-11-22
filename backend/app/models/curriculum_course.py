
from dataclasses import dataclass


@dataclass(kw_only=True)
class CurriculumCourse:
    """A course linked to a curriculum; the SQL key uses both IDs."""

    curriculumId: str
    courseId: str
    courseType: str
