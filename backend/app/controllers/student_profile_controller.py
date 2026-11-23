
"""Student self-service profile HTTP endpoints."""

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

from app.services.student_profile_service import (
    StudentContactValidationError,
    StudentProfileNotFoundError,
    StudentProfileService,
)


student_profile_bp = Blueprint(
    "student_profile",
    __name__,
)

logger = logging.getLogger(__name__)


def _service() -> StudentProfileService:
    return (
        current_app.extensions.get(
            "sms_student_profile_service"
        )
        or StudentProfileService()
    )


@student_profile_bp.after_request
def prevent_profile_caching(response):
    response.headers["Cache-Control"] = "no-store"
    return response


@student_profile_bp.get("/profile")
@roles_required("Student")
def view_profile():
    try:
        profile = _service().view_profile(
            g.auth_principal.user_id
        )

        return jsonify(profile=profile), 200

    except StudentProfileNotFoundError:
        return jsonify(
            error="Student profile not found."
        ), 404

    except Exception:
        logger.exception("Cannot retrieve student profile.")

        return jsonify(
            error="Cannot retrieve student profile at this time."
        ), 503


@student_profile_bp.put("/profile")
@roles_required("Student")
def update_profile():
    try:
        if not request_has_approved_origin():
            return jsonify(
                error="Request origin not allowed."
            ), 403

        raw_token = request.cookies.get(
            SESSION_COOKIE_NAME
        )

        if not raw_token or not validate_csrf(raw_token):
            return jsonify(
                error="Invalid CSRF token."
            ), 403

        if not request.is_json:
            return jsonify(
                error="JSON request required."
            ), 415

        payload = request.get_json(silent=True)

        if not isinstance(payload, dict):
            return jsonify(
                error="Invalid contact information."
            ), 400

        profile = _service().update_information(
            g.auth_principal.user_id,
            payload,
        )

        return jsonify(
            message="Contact information updated successfully.",
            profile=profile,
        ), 200

    except StudentContactValidationError as exc:
        return jsonify(error=str(exc)), 400

    except StudentProfileNotFoundError:
        return jsonify(
            error="Student profile not found."
        ), 404

    except Exception:
        logger.exception("Cannot update student profile.")

        return jsonify(
            error="Cannot update student profile at this time."
        ), 503
