
"""Administrator Student Management HTTP API - Use Cases 13, 14 and 15."""

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

from app.repositories.student_repository import (
    StudentDataIntegrityError,
    StudentDuplicateCitizenIdError,
)

from app.services.admin_student_service import (
    AdminStudentService,
    StudentNotFoundError,
    StudentValidationError,
)


admin_students_bp = Blueprint(
    "admin_students",
    __name__,
)

logger = logging.getLogger(__name__)


def _service() -> AdminStudentService:
    return (
        current_app.extensions.get(
            "sms_admin_student_service"
        )
        or AdminStudentService()
    )


def _query_int(name: str, default: int) -> int:
    raw = request.args.get(name, str(default))

    if not raw.isdecimal():
        raise ValueError(
            f"{name} must be a non-negative integer."
        )

    return int(raw)


def _validate_write_security():
    """Validate approved Origin and session-bound CSRF token."""

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

    return None


@admin_students_bp.after_request
def prevent_personal_data_caching(response):
    response.headers["Cache-Control"] = "no-store"
    return response


# =============================================
# USE CASE 13 - VIEW STUDENT RECORDS
# =============================================

@admin_students_bp.get("/students")
@roles_required("Administrator")
def list_students():

    try:
        limit = _query_int("limit", 10)
        offset = _query_int("offset", 0)
        search = request.args.get("search", "")

        if (
            not 1 <= limit <= 100
            or offset > 1_000_000
            or len(search.strip()) > 100
        ):
            raise ValueError(
                "Invalid pagination or search parameters."
            )

        result = _service().list_records(
            limit=limit,
            offset=offset,
            search=search,
        )

        return jsonify(result), 200

    except ValueError as exc:
        return jsonify(error=str(exc)), 400

    except Exception:
        logger.exception(
            "Failed to retrieve student records."
        )

        return jsonify(
            error="Cannot retrieve student records at this time."
        ), 503


@admin_students_bp.get("/students/<string:student_id>")
@roles_required("Administrator")
def get_student(student_id: str):

    try:
        result = _service().get_record(
            student_id
        )

        return jsonify(student=result), 200

    except StudentNotFoundError:
        return jsonify(
            error="Student record not found."
        ), 404

    except ValueError as exc:
        return jsonify(error=str(exc)), 400

    except Exception:
        logger.exception(
            "Failed to retrieve student record."
        )

        return jsonify(
            error="Cannot retrieve student record at this time."
        ), 503


# =============================================
# USE CASE 14 - UPDATE STUDENT RECORDS
# =============================================

@admin_students_bp.put("/students/<string:student_id>")
@roles_required("Administrator")
def update_student(student_id: str):

    security_error = _validate_write_security()

    if security_error is not None:
        return security_error

    if not request.is_json:
        return jsonify(
            error="JSON request required."
        ), 415

    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        return jsonify(
            error="Invalid student data."
        ), 400

    try:
        updated_student = _service().update_record(
            student_id,
            payload,
        )

        return jsonify(
            message="Student record updated successfully.",
            student=updated_student,
        ), 200

    except StudentNotFoundError:
        return jsonify(
            error="Student record not found."
        ), 404

    except StudentDuplicateCitizenIdError as exc:
        return jsonify(
            error=str(exc)
        ), 409

    except StudentDataIntegrityError as exc:
        return jsonify(
            error=str(exc)
        ), 409

    except StudentValidationError as exc:
        return jsonify(
            error=str(exc)
        ), 400

    except ValueError as exc:
        return jsonify(
            error=str(exc)
        ), 400

    except Exception:
        logger.exception(
            "Failed to update student record."
        )

        return jsonify(
            error="Cannot update student record at this time."
        ), 503


# =============================================
# USE CASE 15 - DELETE STUDENT RECORDS
# =============================================

@admin_students_bp.delete("/students/<string:student_id>")
@roles_required("Administrator")
def delete_student(student_id: str):

    security_error = _validate_write_security()

    if security_error is not None:
        return security_error

    try:
        _service().delete_record(
            student_id
        )

        return jsonify(
            message="Student record deleted successfully."
        ), 200

    except StudentNotFoundError:
        return jsonify(
            error="Student record not found."
        ), 404

    except StudentDataIntegrityError as exc:
        return jsonify(
            error=str(exc)
        ), 409

    except ValueError as exc:
        return jsonify(
            error=str(exc)
        ), 400

    except Exception:
        logger.exception(
            "Failed to delete student record."
        )

        return jsonify(
            error="Cannot delete student record at this time."
        ), 503
