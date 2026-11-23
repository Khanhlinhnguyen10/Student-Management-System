
"""Change Password Controller - Group 05.

Use Case: Change Password
Allowed roles: Student and Lecturer.
"""

import logging

from flask import (
    Blueprint,
    current_app,
    g,
    jsonify,
    request,
)

from app.controllers.auth_security import (
    SESSION_COOKIE_NAME,
    request_has_approved_origin,
    roles_required,
    validate_csrf,
)

from app.repositories.change_password_repository import (
    ChangePasswordRepository,
)

from app.services.change_password_service import (
    ChangePasswordService,
    IncorrectCurrentPasswordError,
    PasswordChangeError,
    PasswordUpdateConflictError,
)


logger = logging.getLogger(__name__)

change_password_bp = Blueprint(
    "change_password",
    __name__,
)


# =============================================
# SERVICE
# =============================================

def _service():
    """Support unit-test injection."""
    service = current_app.extensions.get(
        "sms_change_password_service"
    )

    if service is not None:
        return service

    return ChangePasswordService(
        ChangePasswordRepository()
    )


# =============================================
# PREVENT CACHING
# =============================================

@change_password_bp.after_request
def prevent_caching(response):
    response.headers["Cache-Control"] = "no-store"
    return response


# =============================================
# CHANGE PASSWORD API
# =============================================

@change_password_bp.post("/change-password")
@roles_required("Student", "Lecturer")
def change_password():
    """
    POST /api/auth/change-password

    JSON body:
    {
        "currentPassword": "...",
        "newPassword": "...",
        "confirmPassword": "..."
    }
    """

    # Verify request origin.
    if not request_has_approved_origin():
        return jsonify(
            error="Request origin not allowed."
        ), 403

    # Validate CSRF token bound to current session.
    raw_token = request.cookies.get(
        SESSION_COOKIE_NAME
    )

    if not raw_token or not validate_csrf(raw_token):
        return jsonify(
            error="Invalid CSRF token."
        ), 403

    # Require a JSON request.
    if not request.is_json:
        return jsonify(
            error="JSON request required."
        ), 415

    # Limit request size.
    if (
        request.content_length is not None
        and request.content_length > 4096
    ):
        return jsonify(
            error="Request too large."
        ), 413

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify(
            error="Invalid JSON object."
        ), 400

    try:
        # Identity comes from the verified SQL session.
        # Never accept userId from the request body.
        user_id = g.auth_principal.user_id

        result = _service().change_password(
            user_id=user_id,
            current_password=data.get(
                "currentPassword"
            ),
            new_password=data.get(
                "newPassword"
            ),
            confirm_password=data.get(
                "confirmPassword"
            ),
        )

        return jsonify(result), 200

    except IncorrectCurrentPasswordError:
        return jsonify(
            error="Current password is incorrect."
        ), 400

    except PasswordUpdateConflictError:
        return jsonify(
            error="Password changed during the request. "
                  "Please try again."
        ), 409

    except PasswordChangeError as exc:
        return jsonify(
            error=str(exc)
        ), 400

    except Exception:
        logger.exception(
            "Change Password operation failed."
        )

        return jsonify(
            error="Unable to change password at this time."
        ), 503
