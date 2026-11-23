
"""Administrator-only Semester Management HTTP endpoints."""

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

from app.repositories.admin_semester_repository import (
    SemesterConflictError,
    SemesterNotFoundError,
)

from app.services.admin_semester_service import (
    AdminSemesterService,
)


admin_semester_bp = Blueprint(
    "admin_semester",
    __name__,
)

logger = logging.getLogger(__name__)


@admin_semester_bp.after_request
def disable_cache(response):
    response.headers["Cache-Control"] = "no-store"
    return response


def _service():
    return (
        current_app.extensions.get(
            "sms_admin_semester_service"
        )
        or AdminSemesterService()
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
# GET: LIST SEMESTERS
# =========================================

@admin_semester_bp.get("")
@roles_required("Administrator")
def list_semesters():
    try:
        semesters = (
            _service().list_semesters()
        )

        return jsonify(
            semesters=semesters
        ), 200

    except Exception:
        logger.exception(
            "Failed to list semesters."
        )

        return jsonify(
            error="Unable to load semesters."
        ), 503


# =========================================
# GET: SEMESTER DETAILS
# =========================================

@admin_semester_bp.get("/<semester_id>")
@roles_required("Administrator")
def get_semester(semester_id):
    try:
        result = (
            _service().get_semester(
                semester_id
            )
        )

        if result is None:
            return jsonify(
                error="Semester not found."
            ), 404

        return jsonify(
            semester=result
        ), 200

    except ValueError as exc:
        return jsonify(
            error=str(exc)
        ), 400

    except Exception:
        logger.exception(
            "Failed to retrieve semester."
        )

        return jsonify(
            error="Unable to load semester."
        ), 503


# =========================================
# POST: CREATE SEMESTER
# =========================================

@admin_semester_bp.post("")
@roles_required("Administrator")
def create_semester():
    failure = _check_write()

    if failure is not None:
        return failure

    data, failure = _payload()

    if failure is not None:
        return failure

    try:
        semester_id = (
            _service().create_semester(data)
        )

        return jsonify(
            message="Semester created successfully.",
            semesterId=semester_id,
        ), 201

    except ValueError as exc:
        return jsonify(
            error=str(exc)
        ), 400

    except SemesterConflictError as exc:
        return jsonify(
            error=str(exc)
        ), 409

    except Exception:
        logger.exception(
            "Failed to create semester."
        )

        return jsonify(
            error="Unable to create semester."
        ), 503


# =========================================
# PUT: UPDATE SEMESTER
# =========================================

@admin_semester_bp.put("/<semester_id>")
@roles_required("Administrator")
def update_semester(semester_id):
    failure = _check_write()

    if failure is not None:
        return failure

    data, failure = _payload()

    if failure is not None:
        return failure

    try:
        updated_id = (
            _service().update_semester(
                semester_id,
                data,
            )
        )

        return jsonify(
            message="Semester updated successfully.",
            semesterId=updated_id,
        ), 200

    except ValueError as exc:
        return jsonify(
            error=str(exc)
        ), 400

    except SemesterNotFoundError as exc:
        return jsonify(
            error=str(exc)
        ), 404

    except SemesterConflictError as exc:
        return jsonify(
            error=str(exc)
        ), 409

    except Exception:
        logger.exception(
            "Failed to update semester."
        )

        return jsonify(
            error="Unable to update semester."
        ), 503


# =========================================
# DELETE: DELETE SEMESTER
# =========================================

@admin_semester_bp.delete("/<semester_id>")
@roles_required("Administrator")
def delete_semester(semester_id):
    failure = _check_write()

    if failure is not None:
        return failure

    try:
        _service().delete_semester(
            semester_id
        )

        return jsonify(
            message="Semester deleted successfully."
        ), 200

    except ValueError as exc:
        return jsonify(
            error=str(exc)
        ), 400

    except SemesterNotFoundError as exc:
        return jsonify(
            error=str(exc)
        ), 404

    except SemesterConflictError as exc:
        return jsonify(
            error=str(exc)
        ), 409

    except Exception:
        logger.exception(
            "Failed to delete semester."
        )

        return jsonify(
            error="Unable to delete semester."
        ), 503
