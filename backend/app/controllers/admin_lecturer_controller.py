
"""Administrator Lecturer Management HTTP Controller - Group 05.

Routes:
GET    /api/admin/lecturers
GET    /api/admin/lecturers/faculties
GET    /api/admin/lecturers/<lecturer_id>
PUT    /api/admin/lecturers/<lecturer_id>
DELETE /api/admin/lecturers/<lecturer_id>

Only Administrator may use these endpoints.
Business rules belong to AdminLecturerService.
Database operations belong to AdminLecturerRepository.
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

from app.repositories.admin_lecturer_repository import (
    LecturerDataIntegrityError,
    LecturerDuplicateIdentityError,
)

from app.services.admin_lecturer_service import (
    AdminLecturerService,
    LecturerNotFoundError,
    LecturerValidationError,
)


logger = logging.getLogger(__name__)

admin_lecturers_bp = Blueprint(
    "admin_lecturers",
    __name__,
    url_prefix="/api/admin/lecturers",
)

MAX_REQUEST_BYTES = 4096


# =========================================
# SERVICE ACCESS
# =========================================

def _service() -> AdminLecturerService:
    """Allow unit tests to inject a mock service."""

    injected = current_app.extensions.get(
        "sms_admin_lecturer_service"
    )

    if injected is not None:
        return injected

    return AdminLecturerService()


# =========================================
# RESPONSE HELPERS
# =========================================

def _error(message: str, status: int):
    return jsonify(error=message), status


def _unavailable():
    logger.exception(
        "Administrator Lecturer Management operation failed."
    )

    return _error(
        "Lecturer management service is temporarily unavailable.",
        503,
    )


def _validate_write_request():
    """Validate Origin and session-bound CSRF for PUT/DELETE.

    The @roles_required decorator authenticates the session
    before this function is called.
    """

    if not request_has_approved_origin():
        return _error(
            "Request origin not allowed.",
            403,
        )

    raw_token = request.cookies.get(
        SESSION_COOKIE_NAME
    )

    if not raw_token:
        return _error(
            "Authentication required.",
            401,
        )

    if not validate_csrf(raw_token):
        return _error(
            "Invalid CSRF token.",
            403,
        )

    return None


def _parse_pagination():
    """Return validated limit, offset, search parameters."""

    limit_text = request.args.get(
        "limit", "10"
    )

    offset_text = request.args.get(
        "offset", "0"
    )

    search = request.args.get(
        "search", ""
    )

    if (
        not limit_text.isdecimal()
        or not offset_text.isdecimal()
    ):
        raise LecturerValidationError(
            "Limit and offset must be non-negative integers."
        )

    limit = int(limit_text)
    offset = int(offset_text)

    if not 1 <= limit <= 100:
        raise LecturerValidationError(
            "Limit must be between 1 and 100."
        )

    if offset < 0:
        raise LecturerValidationError(
            "Offset must be non-negative."
        )

    if len(search.strip()) > 100:
        raise LecturerValidationError(
            "Search must not exceed 100 characters."
        )

    return limit, offset, search.strip()


# =========================================
# NO CACHE FOR PERSONAL RECORDS
# =========================================

@admin_lecturers_bp.after_request
def prevent_caching(response):
    response.headers["Cache-Control"] = "no-store"
    return response


# =========================================
# GET LECTURER LIST
# =========================================

@admin_lecturers_bp.get("")
@roles_required("Administrator")
def list_lecturers():
    """Retrieve a paginated lecturer list."""

    try:
        limit, offset, search = _parse_pagination()

        result = _service().list_records(
            limit=limit,
            offset=offset,
            search=search,
        )

        return jsonify(result), 200

    except LecturerValidationError as exc:
        return _error(str(exc), 400)

    except Exception:
        return _unavailable()


# =========================================
# GET FACULTY OPTIONS
# =========================================

@admin_lecturers_bp.get("/faculties")
@roles_required("Administrator")
def list_faculties():
    """Return existing faculties for lecturer editing."""

    try:
        faculties = (
            _service().list_faculty_options()
        )

        return jsonify(
            items=faculties
        ), 200

    except Exception:
        return _unavailable()


# =========================================
# GET LECTURER DETAILS
# =========================================

@admin_lecturers_bp.get("/<lecturer_id>")
@roles_required("Administrator")
def get_lecturer(lecturer_id):
    """Retrieve one lecturer by the immutable Lecturer ID."""

    try:
        record = _service().get_record(
            lecturer_id
        )

        return jsonify(
            lecturer=record
        ), 200

    except LecturerValidationError as exc:
        return _error(str(exc), 400)

    except LecturerNotFoundError as exc:
        return _error(str(exc), 404)

    except Exception:
        return _unavailable()


# =========================================
# UPDATE LECTURER
# =========================================

@admin_lecturers_bp.put("/<lecturer_id>")
@roles_required("Administrator")
def update_lecturer(lecturer_id):
    """Update personal details and affiliated faculty.

    Lecturer ID and User ID cannot be changed.
    """

    security_error = _validate_write_request()

    if security_error is not None:
        return security_error

    if (
        request.content_length is not None
        and request.content_length > MAX_REQUEST_BYTES
    ):
        return _error(
            "Request too large.",
            413,
        )

    if not request.is_json:
        return _error(
            "JSON request required.",
            415,
        )

    payload = request.get_json(
        silent=True
    )

    if not isinstance(payload, dict):
        return _error(
            "Invalid JSON object.",
            400,
        )

    try:
        updated = _service().update_record(
            lecturer_id,
            payload,
        )

        return jsonify(
            message="Lecturer profile updated successfully.",
            lecturer=updated,
        ), 200

    except LecturerValidationError as exc:
        return _error(str(exc), 400)

    except LecturerNotFoundError as exc:
        return _error(str(exc), 404)

    except LecturerDuplicateIdentityError as exc:
        return _error(str(exc), 409)

    except LecturerDataIntegrityError as exc:
        return _error(str(exc), 409)

    except Exception:
        return _unavailable()


# =========================================
# DELETE LECTURER
# =========================================

@admin_lecturers_bp.delete("/<lecturer_id>")
@roles_required("Administrator")
def delete_lecturer(lecturer_id):
    """Delete lecturer and associated account when permitted.

    The user interface must show a confirmation dialog.
    The service and repository enforce data integrity.
    """

    security_error = _validate_write_request()

    if security_error is not None:
        return security_error

    try:
        _service().delete_record(
            lecturer_id
        )

        return jsonify(
            message="Lecturer deleted successfully.",
            lecturerId=lecturer_id,
        ), 200

    except LecturerValidationError as exc:
        return _error(str(exc), 400)

    except LecturerNotFoundError as exc:
        return _error(str(exc), 404)

    except LecturerDataIntegrityError as exc:
        return _error(str(exc), 409)

    except Exception:
        return _unavailable()
