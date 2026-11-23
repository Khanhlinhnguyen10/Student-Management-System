
"""Lecturer sections and gradebook HTTP endpoints."""

import hashlib
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
from app.services.lecturer_sections_service import (
    LecturerSectionsService,
)
from app.services.lecturer_gradebook_service import (
    LecturerGradebookService,
)


lecturer_sections_bp = Blueprint(
    "lecturer_sections",
    __name__,
)

logger = logging.getLogger(__name__)


@lecturer_sections_bp.after_request
def prevent_caching(response):
    response.headers["Cache-Control"] = "no-store"
    return response


def get_gradebook_service():
    return (
        current_app.extensions.get(
            "sms_lecturer_gradebook_service"
        )
        or LecturerGradebookService()
    )


def parse_write_request():
    """Apply origin, CSRF and JSON checks to grade writes."""

    if not request_has_approved_origin():
        return None, None, (
            jsonify(error="Request origin not allowed."),
            403,
        )

    raw_token = request.cookies.get(
        SESSION_COOKIE_NAME, ""
    )

    if not raw_token or not validate_csrf(raw_token):
        return None, None, (
            jsonify(error="Invalid CSRF token."),
            403,
        )

    if (
        request.content_length is not None
        and request.content_length > 4096
    ):
        return None, None, (
            jsonify(error="Request too large."),
            413,
        )

    if not request.is_json:
        return None, None, (
            jsonify(error="JSON request required."),
            415,
        )

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return None, None, (
            jsonify(error="Invalid JSON object."),
            400,
        )

    return data, raw_token, None


# -----------------------------------
# GET: Lecturer assigned class sections
# -----------------------------------

@lecturer_sections_bp.get("/sections")
@roles_required("Lecturer")
def list_assigned_sections():
    try:
        service = (
            current_app.extensions.get(
                "sms_lecturer_sections_service"
            )
            or LecturerSectionsService()
        )

        sections = service.list_assigned_sections(
            g.auth_principal.user_id
        )

        return jsonify(sections=sections), 200

    except ValueError:
        return jsonify(
            error="Invalid Lecturer session."
        ), 400

    except Exception:
        logger.exception(
            "Failed to load Lecturer sections."
        )
        return jsonify(
            error="Unable to load assigned sections."
        ), 503


# -----------------------------------
# GET: Gradebook for assigned class
# -----------------------------------

@lecturer_sections_bp.get(
    "/sections/<section_id>/gradebook"
)
@roles_required("Lecturer")
def get_section_gradebook(section_id):
    try:
        result = get_gradebook_service().get_section_gradebook(
            g.auth_principal.user_id,
            section_id,
        )

        if result is None:
            return jsonify(
                error="Class section not found."
            ), 404

        return jsonify(result), 200

    except ValueError as exc:
        return jsonify(error=str(exc)), 400

    except Exception:
        logger.exception(
            "Failed to load Lecturer gradebook."
        )
        return jsonify(
            error="Unable to load class gradebook."
        ), 503


# -----------------------------------
# PUT: Save Draft
# -----------------------------------

@lecturer_sections_bp.put(
    "/sections/<section_id>/gradebook/<enrollment_id>"
)
@roles_required("Lecturer")
def save_gradebook_draft(section_id, enrollment_id):
    data, _, failure = parse_write_request()

    if failure is not None:
        return failure

    try:
        result = get_gradebook_service().save_draft(
            g.auth_principal.user_id,
            section_id,
            enrollment_id,
            data,
        )

        return jsonify(
            message="Draft grades saved successfully.",
            gradebook=result,
        ), 200

    except ValueError as exc:
        return jsonify(error=str(exc)), 400

    except LookupError:
        return jsonify(
            error="Enrollment not found."
        ), 404

    except PermissionError:
        return jsonify(
            error="Finalized grades cannot be saved as draft."
        ), 409

    except Exception:
        logger.exception(
            "Failed to save Lecturer draft."
        )
        return jsonify(
            error="Unable to save draft grades."
        ), 503


# -----------------------------------
# PUT: Finalize Gradebook
# -----------------------------------

@lecturer_sections_bp.put(
    "/sections/<section_id>/gradebook/"
    "<enrollment_id>/finalize"
)
@roles_required("Lecturer")
def save_final_grade(section_id, enrollment_id):
    data, raw_token, failure = parse_write_request()

    if failure is not None:
        return failure

    try:
        token_hash = hashlib.sha256(
            raw_token.encode("ascii")
        ).hexdigest()
    except UnicodeEncodeError:
        return jsonify(
            error="Invalid session token."
        ), 401

    try:
        result = get_gradebook_service().save_final(
            g.auth_principal.user_id,
            token_hash,
            section_id,
            enrollment_id,
            data,
        )

        return jsonify(
            message="Grades saved and GPA recalculated.",
            gradebook=result,
        ), 200

    except ValueError as exc:
        return jsonify(error=str(exc)), 400

    except LookupError:
        return jsonify(
            error="Enrollment not found in assigned class."
        ), 404

    except PermissionError as exc:
        # A finalized gradebook is a state conflict,
        # not an authentication failure.
        if str(exc) == "Cannot modify finalized grades.":
            return jsonify(
                error="Finalized grades cannot be modified."
            ), 409

        return jsonify(
            error="Active Lecturer session required."
        ), 401

    except Exception:
        logger.exception(
            "Failed to finalize Lecturer gradebook."
        )
        return jsonify(
            error="Unable to save grades."
        ), 503
