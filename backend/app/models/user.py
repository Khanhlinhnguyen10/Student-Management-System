
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date


@dataclass(kw_only=True)
class User(ABC):
    """Abstract user model based on the final Group 05 requirement."""

    userId: str
    username: str
    passwordHash: str = field(repr=False)
    isLocked: bool
    citizenId: str
    fullName: str
    dateOfBirth: date | None = None
    email: str | None = None
    gender: str | None = None
    phoneNumber: str | None = None

    @abstractmethod
    def logIn(self, username: str, password: str) -> bool:
        """Authentication is implemented later by AuthService."""
        raise NotImplementedError("Login is not implemented yet.")

    def logOut(self) -> None:
        raise NotImplementedError("Logout is not implemented yet.")

    def changePassword(self) -> bool:
        raise NotImplementedError("Change Password is not implemented yet.")

    def recoverPassword(self) -> bool:
        raise NotImplementedError("Recover Password is not implemented yet.")
