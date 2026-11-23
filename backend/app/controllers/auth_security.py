
"""HTTP security helpers for Group 05 Authentication API.

These helpers provide cookie-session checks, CSRF protection,
role authorization and a local development login rate limiter.
"""

from collections import deque
from functools import wraps
import hashlib
import hmac
import threading
import time
from urllib.parse import urlsplit

from flask import current_app, g, jsonify, request

from app.services.auth_service import AuthService, SessionExpiredError


SESSION_COOKIE_NAME = "sms_auth"

_ALLOWED_ROLES = frozenset({
    "Administrator",
    "Student",
    "Lecturer",
})


class LoginAttemptLimiter:
    """Limit login attempts per IP within a time window.

    This is an in-memory development limiter. A multi-worker
    production deployment requires shared rate-limit storage.
    """

    def __init__(
        self,
        limit: int = 10,
        window_seconds: int = 60,
    ):
        if type(limit) is not int or limit < 1:
            raise ValueError(
                "Login attempt limit must be a positive integer."
            )

        if type(window_seconds) is not int or window_seconds < 1:
            raise ValueError(
                "Rate-limit window must be a positive integer."
            )

        self.limit = limit
        self.window_seconds = window_seconds
        self._attempts: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def allow(self, client_ip: str) -> bool:
        now = time.monotonic()

        with self._lock:
            if len(self._attempts) >= 1024:
                for ip, attempts in list(self._attempts.items()):
                    if (
                        not attempts
                        or now - attempts[-1] >= self.window_seconds
                    ):
                        del self._attempts[ip]

            attempts = self._attempts.setdefault(
                client_ip, deque()
            )

            while (
                attempts
                and now - attempts[0] >= self.window_seconds
            ):
                attempts.popleft()

            if len(attempts) >= self.limit:
                return False

            attempts.append(now)
            return True


def get_auth_service() -> AuthService:
    """Use a test-injected service or the real AuthService."""
    return (
        current_app.extensions.get("sms_auth_service")
        or AuthService()
    )


def _origin_of_url(url: str) -> str | None:
    try:
        result = urlsplit(url)

        if result.scheme not in ("http", "https"):
            return None

        if not result.hostname:
            return None

        port = result.port
        hostname = result.hostname.lower()

    except ValueError:
        return None

    if (
        (result.scheme == "http" and port == 80)
        or (result.scheme == "https" and port == 443)
    ):
        port = None

    return (
        f"{result.scheme}://{hostname}"
        + (f":{port}" if port else "")
    )


def request_has_approved_origin() -> bool:
    """Check the request's Origin or Referer."""
    expected = _origin_of_url(
        current_app.config["AUTH_ALLOWED_ORIGIN"]
    )

    if expected is None:
        raise RuntimeError(
            "AUTH_ALLOWED_ORIGIN is not configured correctly."
        )

    origin = request.headers.get("Origin")

    if origin is not None:
        try:
            parsed = urlsplit(origin)
        except ValueError:
            return False

        return (
            origin != "null"
            and not parsed.path
            and not parsed.query
            and not parsed.fragment
            and not parsed.username
            and not parsed.password
            and _origin_of_url(origin) == expected
        )

    referer = request.headers.get("Referer")

    return (
        bool(referer)
        and _origin_of_url(referer) == expected
    )


def csrf_token_for_session(raw_session_token: str) -> str:
    """Create a CSRF token bound to the authenticated session."""
    secret = current_app.config["SECRET_KEY"]

    if not isinstance(secret, (str, bytes)) or not secret:
        raise RuntimeError(
            "Flask SECRET_KEY is not configured."
        )

    key = (
        secret.encode("utf-8")
        if isinstance(secret, str)
        else secret
    )

    payload = (
        "SMS_Group05_CSRF_v1:" + raw_session_token
    ).encode("ascii")

    return hmac.new(
        key,
        payload,
        hashlib.sha256,
    ).hexdigest()


def validate_csrf(raw_session_token: str) -> bool:
    submitted = request.headers.get("X-CSRF-Token", "")

    if len(submitted) != 64:
        return False

    expected = csrf_token_for_session(raw_session_token)

    return hmac.compare_digest(submitted, expected)


def roles_required(*roles: str):
    """Protect an API endpoint with real SQL-backed RBAC."""
    if (
        not roles
        or not set(roles).issubset(_ALLOWED_ROLES)
    ):
        raise ValueError(
            "roles_required expects canonical Group 05 roles."
        )

    def decorator(view):
        @wraps(view)
        def guarded(*args, **kwargs):
            raw_token = request.cookies.get(
                SESSION_COOKIE_NAME
            )

            if not raw_token:
                return jsonify(
                    error="Authentication required."
                ), 401

            try:
                principal = (
                    get_auth_service().current_user(raw_token)
                )

            except SessionExpiredError:
                response = jsonify(
                    error="Session expired or invalid."
                )
                response.status_code = 401

                response.delete_cookie(
                    SESSION_COOKIE_NAME,
                    path="/api",
                )

                return response

            except Exception:
                current_app.logger.exception(
                    "Protected API session check failed."
                )

                return jsonify(
                    error="Authentication service temporarily unavailable."
                ), 503

            if principal.role not in roles:
                return jsonify(
                    error="Access denied."
                ), 403

            g.auth_principal = principal
            return view(*args, **kwargs)

        return guarded

    return decorator
