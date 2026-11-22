
"""Group 05 Login / Logout / 15-minute session / RBAC business logic.

No Flask routes or browser token storage are created here. The HTTP layer
provides HttpOnly cookies, CSRF defenses, HTTPS and rate limiting.
"""

from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import re
import secrets

from werkzeug.security import (
    check_password_hash,
    generate_password_hash,
)

from app.repositories.auth_repository import AuthRepository


class AuthenticationError(ValueError):
    """Deliberately identical response for invalid credentials or role."""


class SessionExpiredError(PermissionError):
    """Unknown, revoked, locked, or expired login session."""


class AccessDeniedError(PermissionError):
    """Authenticated user does not have the required role."""


class PasswordChangeError(ValueError):
    """Invalid password input or incorrect current password."""


class PasswordChangeConflictError(RuntimeError):
    """Password or account state changed during the request."""


@dataclass(frozen=True, slots=True)
class LoginResult:
    """Internal result. Never serialize token outside cookie controls."""

    token: str = field(repr=False)
    user_id: str
    username: str
    full_name: str
    role: str
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class AuthPrincipal:
    user_id: str
    username: str
    full_name: str
    role: str
    expires_at: datetime


_ROLE_INPUTS = {
    "admin": "Administrator",
    "administrator": "Administrator",
    "student": "Student",
    "lecturer": "Lecturer",
}

_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_-]{43}\Z")

_GENERIC_LOGIN_ERROR = "Thông tin đăng nhập không hợp lệ."

# Implementation policy pending final confirmation.
_PASSWORD_MIN_LENGTH = 8
_PASSWORD_MAX_LENGTH = 128


class AuthService:
    def __init__(
        self,
        repository: AuthRepository | None = None,
    ):
        self._repository = (
            repository
            if repository is not None
            else AuthRepository()
        )

    @staticmethod
    def _role(role: str) -> str | None:
        if not isinstance(role, str):
            return None

        return _ROLE_INPUTS.get(
            role.strip().lower()
        )

    @staticmethod
    def _hash_token(raw_token: str) -> str:
        if (
            not isinstance(raw_token, str)
            or not _TOKEN_PATTERN.fullmatch(raw_token)
        ):
            raise SessionExpiredError(
                "Phiên đăng nhập không hợp lệ hoặc đã hết hạn."
            )

        return hashlib.sha256(
            raw_token.encode("ascii")
        ).hexdigest()

    # =========================================
    # LOGIN
    # =========================================

    def login(
        self,
        username: str,
        password: str,
        selected_role: str,
    ) -> LoginResult:
        """Login using valid credentials and exactly one assigned role."""

        role = self._role(selected_role)

        if (
            role is None
            or not isinstance(username, str)
            or not 1 <= len(username.strip()) <= 50
            or not isinstance(password, str)
            or not password
        ):
            raise AuthenticationError(
                _GENERIC_LOGIN_ERROR
            )

        account = self._repository.get_by_username(
            username.strip()
        )

        if (
            account is None
            or account.is_locked
            or len(account.roles) != 1
        ):
            raise AuthenticationError(
                _GENERIC_LOGIN_ERROR
            )

        try:
            verified = check_password_hash(
                account.password_hash,
                password,
            )
        except (TypeError, ValueError):
            verified = False

        if (
            not verified
            or account.roles[0] != role
        ):
            raise AuthenticationError(
                _GENERIC_LOGIN_ERROR
            )

        raw_token = secrets.token_urlsafe(32)

        token_hash = self._hash_token(
            raw_token
        )

        stored = self._repository.create_session(
            account.user_id,
            token_hash,
        )

        return LoginResult(
            token=raw_token,
            user_id=stored.user_id,
            username=account.username,
            full_name=account.full_name,
            role=role,
            expires_at=stored.expires_at,
        )

    # =========================================
    # CURRENT USER / SESSION
    # =========================================

    def current_user(
        self,
        raw_token: str,
    ) -> AuthPrincipal:
        """Authenticate session and extend its 15-minute expiry."""

        token_hash = self._hash_token(
            raw_token
        )

        stored = self._repository.touch_session(
            token_hash
        )

        if stored is None:
            raise SessionExpiredError(
                "Phiên đăng nhập không hợp lệ hoặc đã hết hạn."
            )

        account = self._repository.get_by_user_id(
            stored.user_id
        )

        if (
            account is None
            or account.is_locked
            or len(account.roles) != 1
        ):
            self._repository.revoke_session(
                token_hash
            )

            raise SessionExpiredError(
                "Phiên đăng nhập không hợp lệ hoặc đã hết hạn."
            )

        return AuthPrincipal(
            user_id=account.user_id,
            username=account.username,
            full_name=account.full_name,
            role=account.roles[0],
            expires_at=stored.expires_at,
        )

    # =========================================
    # ROLE AUTHORIZATION
    # =========================================

    def require_role(
        self,
        raw_token: str,
        required_role: str,
    ) -> AuthPrincipal:
        """Enforce authorization in Backend."""

        expected = self._role(
            required_role
        )

        if expected is None:
            raise ValueError(
                "Unknown required role in Backend configuration."
            )

        principal = self.current_user(
            raw_token
        )

        if principal.role != expected:
            raise AccessDeniedError(
                "Bạn không có quyền thực hiện chức năng này."
            )

        return principal

    # =========================================
    # LOGOUT
    # =========================================

    def logout(
        self,
        raw_token: str,
    ) -> bool:
        """Revoke the SQL-backed session."""

        token_hash = self._hash_token(
            raw_token
        )

        return self._repository.revoke_session(
            token_hash
        )

    # =========================================
    # PASSWORD VALIDATION
    # =========================================

    @staticmethod
    def _validate_new_password(
        password: str,
    ) -> None:
        """Apply the implementation password complexity policy."""

        if not isinstance(password, str):
            raise PasswordChangeError(
                "Mật khẩu mới không hợp lệ."
            )

        if not (
            _PASSWORD_MIN_LENGTH
            <= len(password)
            <= _PASSWORD_MAX_LENGTH
        ):
            raise PasswordChangeError(
                "Mật khẩu mới phải có từ 8 đến 128 ký tự."
            )

        if not (
            any(char.islower() for char in password)
            and any(char.isupper() for char in password)
            and any(char.isdigit() for char in password)
            and any(not char.isalnum() for char in password)
        ):
            raise PasswordChangeError(
                "Mật khẩu mới cần có chữ hoa, chữ thường, "
                "chữ số và ký tự đặc biệt."
            )

    # =========================================
    # CHANGE PASSWORD
    # STUDENT AND LECTURER ONLY
    # =========================================

    def change_password(
        self,
        *,
        principal: AuthPrincipal,
        current_password: str,
        new_password: str,
        confirm_password: str,
    ) -> None:
        """Change password with authorization and concurrency protection.

        The principal must come from a verified SQL-backed session,
        never from user-supplied request JSON.

        Password updates use optimistic concurrency checking in
        AuthRepository and commit before returning successfully.
        """

        # -------------------------------------
        # 1. Verify authenticated principal
        # -------------------------------------

        if not isinstance(
            principal,
            AuthPrincipal,
        ):
            raise AccessDeniedError(
                "Không thể xác thực tài khoản."
            )

        if principal.role not in (
            "Student",
            "Lecturer",
        ):
            raise AccessDeniedError(
                "Bạn không có quyền thực hiện chức năng này."
            )

        # -------------------------------------
        # 2. Validate required input
        # -------------------------------------

        if (
            not isinstance(current_password, str)
            or not current_password
        ):
            raise PasswordChangeError(
                "Vui lòng nhập mật khẩu hiện tại."
            )

        if not isinstance(
            confirm_password,
            str,
        ):
            raise PasswordChangeError(
                "Vui lòng xác nhận mật khẩu mới."
            )

        if new_password != confirm_password:
            raise PasswordChangeError(
                "Xác nhận mật khẩu mới không khớp."
            )

        # -------------------------------------
        # 3. Read account from SQL Server
        # -------------------------------------

        account = self._repository.get_by_user_id(
            principal.user_id
        )

        if (
            account is None
            or account.is_locked
            or len(account.roles) != 1
            or account.roles[0] != principal.role
        ):
            raise AccessDeniedError(
                "Tài khoản không còn hợp lệ hoặc đã bị khóa."
            )

        # -------------------------------------
        # 4. Verify current password
        # -------------------------------------

        try:
            verified = check_password_hash(
                account.password_hash,
                current_password,
            )

        except (TypeError, ValueError):
            verified = False

        if not verified:
            raise PasswordChangeError(
                "Mật khẩu hiện tại không đúng."
            )

        # -------------------------------------
        # 5. Validate new password
        # -------------------------------------

        self._validate_new_password(
            new_password
        )

        if new_password == current_password:
            raise PasswordChangeError(
                "Mật khẩu mới phải khác mật khẩu hiện tại."
            )

        # -------------------------------------
        # 6. Generate password hash
        # -------------------------------------

        new_hash = generate_password_hash(
            new_password
        )

        # -------------------------------------
        # 7. Atomic conditional update
        # -------------------------------------

        updated = (
            self._repository.update_password_if_current(
                user_id=account.user_id,
                old_hash=account.password_hash,
                new_hash=new_hash,
            )
        )

        # -------------------------------------
        # 8. Handle concurrent modification
        # -------------------------------------

        if not updated:
            raise PasswordChangeConflictError(
                "Thông tin tài khoản đã thay đổi. "
                "Vui lòng tải lại và thử lại."
            )
