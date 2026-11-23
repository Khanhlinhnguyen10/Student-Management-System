
"""Authentication API for Group 05.

Login, Logout, session verification and CSRF endpoints.
SQL queries and business logic remain in Repository and Service.
"""

from datetime import timezone
import logging

from flask import (
    Blueprint,
    current_app,
    g,
    jsonify,
    make_response,
    request,
)

from app.controllers.auth_security import (
    SESSION_COOKIE_NAME,
    csrf_token_for_session,
    get_auth_service,
    request_has_approved_origin,
    roles_required,
    validate_csrf,
)

from app.services.auth_service import (
    AuthenticationError,
    SessionExpiredError,
)


logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__)


def _public_user(user) -> dict:
    """Return safe information without session token or password hash."""
    return {
        "userId": user.user_id,
        "username": user.username,
        "fullName": user.full_name,
        "role": user.role,
        "expiresAt": user.expires_at.astimezone(
            timezone.utc
        ).isoformat(),
    }


def _sql_unavailable():
    return jsonify(
        error="Authentication service temporarily unavailable."
    ), 503


@auth_bp.post("/login")
def login():
    """Validate credentials and create a SQL-backed session."""
    if not request_has_approved_origin():
        return jsonify(
            error="Request origin not allowed."
        ), 403

    if not request.is_json:
        return jsonify(
            error="JSON request required."
        ), 415

    if (
        request.content_length is not None
        and request.content_length > 4096
    ):
        return jsonify(
            error="Login request too large."
        ), 413

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify(
            error="Invalid JSON object."
        ), 400

    ip = request.remote_addr or "unknown"

    limiter = current_app.extensions[
        "sms_login_limiter"
    ]

    if not limiter.allow(ip):
        response = jsonify(
            error="Too many login attempts. Please try later."
        )
        response.status_code = 429
        response.headers["Retry-After"] = str(
            limiter.window_seconds
        )
        return response

    try:
        result = get_auth_service().login(
            data.get("username"),
            data.get("password"),
            data.get("role"),
        )

    except AuthenticationError:
        return jsonify(
            error="Thông tin đăng nhập không hợp lệ."
        ), 401

    except Exception:
        logger.exception(
            "Login database operation failed."
        )
        return _sql_unavailable()

    response = make_response(
        jsonify(user=_public_user(result)),
        200,
    )

    response.set_cookie(
        SESSION_COOKIE_NAME,
        result.token,
        httponly=True,
        secure=current_app.config[
            "AUTH_COOKIE_SECURE"
        ],
        samesite="Lax",
        path="/api",
    )

    return response


@auth_bp.get("/me")
@roles_required(
    "Administrator",
    "Student",
    "Lecturer",
)
def me():
    """Return the currently authenticated user."""
    return jsonify(
        user=_public_user(g.auth_principal)
    )


@auth_bp.get("/csrf")
@roles_required(
    "Administrator",
    "Student",
    "Lecturer",
)
def csrf():
    """Create a CSRF token for the active session."""
    raw_token = request.cookies[
        SESSION_COOKIE_NAME
    ]

    return jsonify(
        csrfToken=csrf_token_for_session(raw_token)
    )


@auth_bp.post("/logout")
def logout():
    """Revoke SQL session before confirming Logout."""
    if not request_has_approved_origin():
        return jsonify(
            error="Request origin not allowed."
        ), 403

    raw_token = request.cookies.get(
        SESSION_COOKIE_NAME
    )

    if not raw_token:
        return jsonify(
            error="Authentication required."
        ), 401

    if not validate_csrf(raw_token):
        return jsonify(
            error="Invalid CSRF token."
        ), 403

    try:
        revoked = get_auth_service().logout(
            raw_token
        )

    except SessionExpiredError:
        return jsonify(
            error="Session expired or invalid."
        ), 401

    except Exception:
        logger.exception(
            "Logout database operation failed."
        )
        return _sql_unavailable()

    if not revoked:
        return jsonify(
            error="Session was not active in the database."
        ), 401

    response = make_response(
        jsonify(
            message="Logged out successfully."
        ),
        200,
    )

    response.delete_cookie(
        SESSION_COOKIE_NAME,
        path="/api",
    )

    return response
