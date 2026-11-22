
from dataclasses import dataclass


@dataclass(kw_only=True)
class Faculty:
    """
    Faculty model - Student Management System Group 05.

    Attributes follow the updated official Data Model.
    Operations follow the Class Diagram.
    """

    facultyId: str
    facultyCode: str
    facultyName: str
    email: str | None = None
    phoneNumber: str | None = None

    def createFaculty(self) -> bool:
        """
        Operation declared in the Class Diagram.

        Implementation will use Academic Service
        and Faculty Repository.
        """
        raise NotImplementedError(
            "Create Faculty is not implemented yet."
        )

    def updateFaculty(self) -> bool:
        """
        Update Faculty operation.
        """
        raise NotImplementedError(
            "Update Faculty is not implemented yet."
        )

    def deleteFaculty(self) -> bool:
        """
        Delete Faculty operation.
        """
        raise NotImplementedError(
            "Delete Faculty is not implemented yet."
        )
