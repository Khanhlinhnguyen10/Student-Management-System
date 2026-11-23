
"""Administrator-only Class Section Management HTTP endpoints.

Use Cases 35-39:
- Manage Class Sections
- Create Class Sections
- View Class Sections
- Update Class Sections
- Delete Class Sections

Lecturer assignment remains in Use Case 40.
"""

import logging

from flask import (
    Blueprint,
    current_app,
    jsonify,
    request,
)

from app.controllers.auth_security import (
    SESSION_COOKIE_NAME,
    request_has_approved_origin,
    roles_required,
    validate_csrf,
)

from app.repositories.admin_class_section_repository import (
    ClassSectionConflictError,
    ClassSectionNotFoundError,
)

from app.services.admin_class_section_service import (
    AdminClassSectionService,
)


# ============================================================
# BLUEPRINT
# ============================================================

admin_class_section_bp = Blueprint(
    "admin_class_section",
    __name__,
)

logger = logging.getLogger(__name__)


# ============================================================
# PREVENT CACHING
# ============================================================

@admin_class_section_bp.after_request
def disable_cache(response):
    response.headers["Cache-Control"] = "no-store"
    return response


# ============================================================
# GET SERVICE
# ============================================================

def _service():
    return (
        current_app.extensions.get(
            "sms_admin_class_section_service"
        )
        or AdminClassSectionService()
    )


# ============================================================
# VALIDATE WRITE REQUEST
# ============================================================

def _check_write():
    """Validate origin, active session and CSRF token."""

    if not request_has_approved_origin():
        return (
            jsonify(
                error="Request origin not allowed."
            ),
            403,
        )

    token = request.cookies.get(
        SESSION_COOKIE_NAME,
        "",
    )

    if (
        not token
        or not validate_csrf(token)
    ):
        return (
            jsonify(
                error="Invalid CSRF token."
            ),
            403,
        )

    if (
        request.content_length is not None
        and request.content_length > 4096
    ):
        return (
            jsonify(
                error="Request too large."
            ),
            413,
        )

    return None


# ============================================================
# VALIDATE JSON PAYLOAD
# ============================================================

def _payload():
    """Read and validate a JSON object."""

    if not request.is_json:
        return None, (
            jsonify(
                error="JSON request required."
            ),
            415,
        )

    data = request.get_json(
        silent=True
    )

    if not isinstance(data, dict):
        return None, (
            jsonify(
                error="Invalid JSON object."
            ),
            400,
        )

    return data, None


# ============================================================
# GET - LIST CLASS SECTIONS
# ============================================================

@admin_class_section_bp.get("")
@roles_required("Administrator")
def list_sections():
    """Get all sections or filter by semesterId."""

    try:
        semester_id = request.args.get(
            "semesterId"
        )

        records = _service().list_sections(
            semester_id
        )

        return jsonify(
            sections=records
        ), 200

    except ValueError as exc:
        return jsonify(
            error=str(exc)
        ), 400

    except Exception:
        logger.exception(
            "Failed to list Class Sections."
        )

        return jsonify(
            error="Unable to load Class Sections."
        ), 503


# ============================================================
# GET - SEMESTERS FOR DROPDOWN
# ============================================================

@admin_class_section_bp.get("/semesters")
@roles_required("Administrator")
def list_available_semesters():
    try:
        records = _service().list_semesters()

        return jsonify(
            semesters=records
        ), 200

    except Exception:
        logger.exception(
            "Failed to load Class Section semesters."
        )

        return jsonify(
            error="Unable to load semesters."
        ), 503


# ============================================================
# GET - COURSES FOR DROPDOWN
# ============================================================

@admin_class_section_bp.get("/courses")
@roles_required("Administrator")
def list_available_courses():
    try:
        records = _service().list_courses()

        return jsonify(
            courses=records
        ), 200

    except Exception:
        logger.exception(
            "Failed to load Class Section courses."
        )

        return jsonify(
            error="Unable to load courses."
        ), 503


# ============================================================
# GET - CLASS SECTION DETAILS
# ============================================================

@admin_class_section_bp.get("/<section_id>")
@roles_required("Administrator")
def get_section(section_id):
    try:
        record = _service().get_section(
            section_id
        )

        if record is None:
            return jsonify(
                error="Class Section not found."
            ), 404

        return jsonify(
            section=record
        ), 200

    except ValueError as exc:
        return jsonify(
            error=str(exc)
        ), 400

    except Exception:
        logger.exception(
            "Failed to retrieve Class Section."
        )

        return jsonify(
            error="Unable to load Class Section."
        ), 503


# ============================================================
# POST - CREATE CLASS SECTION
# ============================================================

@admin_class_section_bp.post("")
@roles_required("Administrator")
def create_section():
    failure = _check_write()

    if failure is not None:
        return failure

    data, failure = _payload()

    if failure is not None:
        return failure

    try:
        section_id = _service().create_section(
            data
        )

        return jsonify(
            message="Class Section created successfully.",
            classSectionId=section_id,
        ), 201

    except ValueError as exc:
        return jsonify(
            error=str(exc)
        ), 400

    except ClassSectionConflictError as exc:
        return jsonify(
            error=str(exc)
        ), 409

    except Exception:
        logger.exception(
            "Failed to create Class Section."
        )

        return jsonify(
            error="Unable to create Class Section."
        ), 503


# ============================================================
# PUT - UPDATE CLASS SECTION
# ============================================================

@admin_class_section_bp.put("/<section_id>")
@roles_required("Administrator")
def update_section(section_id):
    failure = _check_write()

    if failure is not None:
        return failure

    data, failure = _payload()

    if failure is not None:
        return failure

    try:
        updated_id = _service().update_section(
            section_id,
            data,
        )

        return jsonify(
            message="Class Section updated successfully.",
            classSectionId=updated_id,
        ), 200

    except ValueError as exc:
        return jsonify(
            error=str(exc)
        ), 400

    except ClassSectionNotFoundError as exc:
        return jsonify(
            error=str(exc)
        ), 404

    except ClassSectionConflictError as exc:
        return jsonify(
            error=str(exc)
        ), 409

    except Exception:
        logger.exception(
            "Failed to update Class Section."
        )

        return jsonify(
            error="Unable to update Class Section."
        ), 503


# ============================================================
# DELETE - DELETE CLASS SECTION
# ============================================================

@admin_class_section_bp.delete("/<section_id>")
@roles_required("Administrator")
def delete_section(section_id):
    failure = _check_write()

    if failure is not None:
        return failure

    try:
        _service().delete_section(
            section_id
        )

        return jsonify(
            message="Class Section deleted successfully."
        ), 200

    except ValueError as exc:
        return jsonify(
            error=str(exc)
        ), 400

    except ClassSectionNotFoundError as exc:
        return jsonify(
            error=str(exc)
        ), 404

    except ClassSectionConflictError as exc:
        return jsonify(
            error=str(exc)
        ), 409

    except Exception:
        logger.exception(
            "Failed to delete Class Section."
        )

        return jsonify(
            error="Unable to delete Class Section."
        ), 503
