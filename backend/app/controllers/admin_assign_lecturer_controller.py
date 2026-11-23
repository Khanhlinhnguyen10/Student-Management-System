
"""Administrator Assign Lecturer API - Group 05.

Use Case 40: Assign Lecturer to Class Sections.

Routes:
GET  /api/admin/assign-lecturer/semesters
GET  /api/admin/assign-lecturer/sections?semesterId=...
GET  /api/admin/assign-lecturer/lecturers
POST /api/admin/assign-lecturer/assign

All routes require Administrator authorization.
The POST route also requires approved Origin and CSRF.
"""

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

from app.repositories.assign_lecturer_repository import (
    AssignmentBusyError,
    AssignmentError,
    AssignmentNotFoundError,
    AssignmentScheduleConflictError,
    AssignmentScheduleError,
)

from app.services.assign_lecturer_service import (
    AssignLecturerService,
    AssignLecturerValidationError,
)


admin_assign_lecturer_bp = Blueprint(
    "admin_assign_lecturer",
    __name__,
    url_prefix="/api/admin/assign-lecturer",
)


def _service() -> AssignLecturerService:
    """Support service injection for unit tests."""
    service = current_app.extensions.get(
        "sms_assign_lecturer_service"
    )

    return (
        service
        if service is not None
        else AssignLecturerService()
    )


def _error(message: str, status: int):
    return jsonify(error=message), status


def _unavailable():
    return _error(
        "Assign Lecturer service is temporarily unavailable.",
        503,
    )


@admin_assign_lecturer_bp.after_request
def disable_cache(response):
    response.headers["Cache-Control"] = "no-store"
    return response


# =========================================
# GET SEMESTERS
# =========================================

@admin_assign_lecturer_bp.get("/semesters")
@roles_required("Administrator")
def list_assignment_semesters():
    try:
        items = _service().list_semesters()
        return jsonify(items=items), 200

    except Exception:
        current_app.logger.exception(
            "Failed to retrieve assignment semesters."
        )
        return _unavailable()


# =========================================
# GET CLASS SECTIONS BY SEMESTER
# =========================================

@admin_assign_lecturer_bp.get("/sections")
@roles_required("Administrator")
def list_assignment_sections():
    semester_id = request.args.get(
        "semesterId",
        "",
    )

    try:
        items = _service().list_sections(
            semester_id
        )

        return jsonify(items=items), 200

    except AssignLecturerValidationError as exc:
        return _error(str(exc), 400)

    except Exception:
        current_app.logger.exception(
            "Failed to retrieve assignment sections."
        )
        return _unavailable()


# =========================================
# GET LECTURERS
# =========================================

@admin_assign_lecturer_bp.get("/lecturers")
@roles_required("Administrator")
def list_assignment_lecturers():
    try:
        items = _service().list_lecturers()
        return jsonify(items=items), 200

    except Exception:
        current_app.logger.exception(
            "Failed to retrieve assignment lecturers."
        )
        return _unavailable()


# =========================================
# POST ASSIGN LECTURER
# =========================================

@admin_assign_lecturer_bp.post("/assign")
@roles_required("Administrator")
def assign_lecturer_to_section():

    # 1. Protect state-changing requests.
    if not request_has_approved_origin():
        return _error(
            "Request origin is not allowed.",
            403,
        )

    raw_token = request.cookies.get(
        SESSION_COOKIE_NAME
    )

    if not raw_token or not validate_csrf(raw_token):
        return _error(
            "Invalid CSRF token.",
            403,
        )

    # 2. Require JSON.
    if not request.is_json:
        return _error(
            "JSON request required.",
            415,
        )

    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        return _error(
            "Invalid JSON object.",
            400,
        )

    # 3. Validate and assign through Service.
    try:
        result = _service().assign_record(payload)

        return jsonify(
            message=(
                "Lecturer assigned successfully."
                if result["changed"]
                else "Lecturer assignment is already up to date."
            ),
            assignment=result,
        ), 200

    except AssignLecturerValidationError as exc:
        return _error(str(exc), 400)

    except AssignmentNotFoundError as exc:
        return _error(str(exc), 404)

    except AssignmentScheduleConflictError as exc:
        return _error(str(exc), 409)

    except AssignmentScheduleError as exc:
        return _error(str(exc), 409)

    except AssignmentBusyError as exc:
        return _error(str(exc), 503)

    except AssignmentError:
        current_app.logger.exception(
            "Assign Lecturer transaction failed."
        )
        return _unavailable()

    except Exception:
        current_app.logger.exception(
            "Unexpected Assign Lecturer operation failure."
        )
        return _unavailable()
