
"""Administrator-only Faculty Management HTTP endpoints."""

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

from app.repositories.admin_faculty_repository import (
    FacultyConflictError,
    FacultyNotFoundError,
)

from app.services.admin_faculty_service import (
    AdminFacultyService,
)


admin_faculty_bp = Blueprint(
    "admin_faculty",
    __name__,
)

logger = logging.getLogger(__name__)


@admin_faculty_bp.after_request
def disable_cache(response):
    response.headers["Cache-Control"] = "no-store"
    return response


def _service():
    return (
        current_app.extensions.get(
            "sms_admin_faculty_service"
        )
        or AdminFacultyService()
    )


# =========================================
# WRITE REQUEST SECURITY
# =========================================

def _check_write():
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

    if not token or not validate_csrf(token):
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


def _payload():
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


# =========================================
# GET: FACULTY LIST
# =========================================

@admin_faculty_bp.get("")
@roles_required("Administrator")
def list_faculties():
    try:
        records = _service().list_faculties()

        return jsonify(
            faculties=records
        ), 200

    except Exception:
        logger.exception(
            "Failed to list faculties."
        )

        return jsonify(
            error="Unable to load faculties."
        ), 503


# =========================================
# GET: FACULTY DETAILS
# =========================================

@admin_faculty_bp.get("/<faculty_id>")
@roles_required("Administrator")
def get_faculty(faculty_id):
    try:
        result = _service().get_faculty(
            faculty_id
        )

        if result is None:
            return jsonify(
                error="Faculty not found."
            ), 404

        return jsonify(
            faculty=result
        ), 200

    except ValueError as exc:
        return jsonify(
            error=str(exc)
        ), 400

    except Exception:
        logger.exception(
            "Failed to retrieve faculty."
        )

        return jsonify(
            error="Unable to load faculty."
        ), 503


# =========================================
# POST: CREATE FACULTY
# =========================================

@admin_faculty_bp.post("")
@roles_required("Administrator")
def create_faculty():
    failure = _check_write()

    if failure is not None:
        return failure

    data, failure = _payload()

    if failure is not None:
        return failure

    try:
        faculty_id = _service().create_faculty(
            data
        )

        return jsonify(
            message="Faculty created successfully.",
            facultyId=faculty_id,
        ), 201

    except ValueError as exc:
        return jsonify(
            error=str(exc)
        ), 400

    except FacultyConflictError as exc:
        return jsonify(
            error=str(exc)
        ), 409

    except Exception:
        logger.exception(
            "Failed to create faculty."
        )

        return jsonify(
            error="Unable to create faculty."
        ), 503


# =========================================
# PUT: UPDATE FACULTY
# =========================================

@admin_faculty_bp.put("/<faculty_id>")
@roles_required("Administrator")
def update_faculty(faculty_id):
    failure = _check_write()

    if failure is not None:
        return failure

    data, failure = _payload()

    if failure is not None:
        return failure

    try:
        updated_id = _service().update_faculty(
            faculty_id,
            data,
        )

        return jsonify(
            message="Faculty updated successfully.",
            facultyId=updated_id,
        ), 200

    except ValueError as exc:
        return jsonify(
            error=str(exc)
        ), 400

    except FacultyNotFoundError as exc:
        return jsonify(
            error=str(exc)
        ), 404

    except FacultyConflictError as exc:
        return jsonify(
            error=str(exc)
        ), 409

    except Exception:
        logger.exception(
            "Failed to update faculty."
        )

        return jsonify(
            error="Unable to update faculty."
        ), 503


# =========================================
# DELETE: DELETE FACULTY
# =========================================

@admin_faculty_bp.delete("/<faculty_id>")
@roles_required("Administrator")
def delete_faculty(faculty_id):
    failure = _check_write()

    if failure is not None:
        return failure

    try:
        _service().delete_faculty(
            faculty_id
        )

        return jsonify(
            message="Faculty deleted successfully."
        ), 200

    except ValueError as exc:
        return jsonify(
            error=str(exc)
        ), 400

    except FacultyNotFoundError as exc:
        return jsonify(
            error=str(exc)
        ), 404

    except FacultyConflictError as exc:
        return jsonify(
            error=str(exc)
        ), 409

    except Exception:
        logger.exception(
            "Failed to delete faculty."
        )

        return jsonify(
            error="Unable to delete faculty."
        ), 503
