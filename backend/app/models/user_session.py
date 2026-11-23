
"""UserSession model - Student Management System Group 05.

Matches the UserSession class in the approved UML Class Diagram.

This model represents session state in memory.
Database session operations remain the responsibility of
AuthService and AuthRepository.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


SESSION_TIMEOUT = timedelta(minutes=15)


def _utc(value: datetime) -> datetime:
    """Normalize timestamps to UTC."""

    if not isinstance(value, datetime):
        raise TypeError(
            "Session timestamps must be datetime values."
        )

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


@dataclass(kw_only=True)
class UserSession:
    sessionId: str
    createdAt: datetime
    lastActivityAt: datetime
    expiresAt: datetime
    isActive: bool = True

    def __post_init__(self) -> None:
        if (
            not isinstance(self.sessionId, str)
            or not self.sessionId.strip()
        ):
            raise ValueError(
                "sessionId must be a nonempty string."
            )

        if not isinstance(self.isActive, bool):
            raise TypeError(
                "isActive must be a Boolean."
            )

        self.createdAt = _utc(self.createdAt)
        self.lastActivityAt = _utc(self.lastActivityAt)
        self.expiresAt = _utc(self.expiresAt)

        if self.lastActivityAt < self.createdAt:
            raise ValueError(
                "lastActivityAt cannot precede createdAt."
            )

        if self.expiresAt <= self.createdAt:
            raise ValueError(
                "expiresAt must be later than createdAt."
            )

    def isExpired(self) -> bool:
        """Check whether the session is expired or inactive."""

        now = datetime.now(timezone.utc)

        return (
            not self.isActive
            or now >= self.expiresAt
        )

    def refresh(self) -> None:
        """Refresh activity and expiry in memory only."""

        if self.isExpired():
            raise ValueError(
                "Cannot refresh an inactive or expired session."
            )

        now = datetime.now(timezone.utc)

        self.lastActivityAt = now
        self.expiresAt = now + SESSION_TIMEOUT

    def terminate(self) -> None:
        """Mark the session inactive in memory only."""

        self.isActive = False
