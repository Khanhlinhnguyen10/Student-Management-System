
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

from app.services.lecturer_profile_service import (
    LecturerProfileService,
)


lecturer_profile_bp = Blueprint(
    "lecturer_profile",
    __name__,
)

logger = logging.getLogger(__name__)


def profile_service():
    return (
        current_app.extensions.get(
            "sms_lecturer_profile_service"
        )
        or LecturerProfileService()
    )


@lecturer_profile_bp.after_request
def no_cache(response):
    response.headers["Cache-Control"] = "no-store"
    return response


@lecturer_profile_bp.get("")
@roles_required("Lecturer")
def get_my_profile():
    try:
        profile = profile_service().get_profile(
            g.auth_principal.user_id
        )

        if profile is None:
            return jsonify(
                error="Lecturer profile not found."
            ), 404

        return jsonify(profile=profile), 200

    except ValueError as exc:
        return jsonify(error=str(exc)), 400

    except Exception:
        logger.exception("Unable to load lecturer profile.")
        return jsonify(
            error="Unable to load lecturer profile."
        ), 503


@lecturer_profile_bp.put("")
@roles_required("Lecturer")
def update_my_profile():
    if not request_has_approved_origin():
        return jsonify(
            error="Request origin not allowed."
        ), 403

    raw_token = request.cookies.get(
        SESSION_COOKIE_NAME, ""
    )

    if not raw_token or not validate_csrf(raw_token):
        return jsonify(
            error="Invalid CSRF token."
        ), 403

    if (
        request.content_length is not None
        and request.content_length > 2048
    ):
        return jsonify(error="Request too large."), 413

    if not request.is_json:
        return jsonify(error="JSON required."), 415

    data = request.get_json(silent=True)

    try:
        profile = profile_service().update_contact(
            g.auth_principal.user_id,
            data,
        )

        return jsonify(
            message="Contact information updated.",
            profile=profile,
        ), 200

    except ValueError as exc:
        return jsonify(error=str(exc)), 400

    except LookupError:
        return jsonify(
            error="Lecturer profile not found."
        ), 404

    except Exception:
        logger.exception("Unable to update lecturer profile.")
        return jsonify(
            error="Unable to update contact information."
        ), 503
