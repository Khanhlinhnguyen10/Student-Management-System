
"""Administrator-only Course Management HTTP endpoints."""

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

from app.repositories.admin_course_repository import (
    CourseConflictError,
    CourseNotFoundError,
)

from app.services.admin_course_service import (
    AdminCourseService,
)


admin_course_bp = Blueprint(
    "admin_course",
    __name__,
)

logger = logging.getLogger(__name__)


# =========================================
# PREVENT BROWSER CACHING
# =========================================

@admin_course_bp.after_request
def disable_cache(response):
    response.headers["Cache-Control"] = "no-store"
    return response


# =========================================
# GET COURSE SERVICE
# =========================================

def _service():
    return (
        current_app.extensions.get(
            "sms_admin_course_service"
        )
        or AdminCourseService()
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


# =========================================
# VALIDATE JSON BODY
# =========================================

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
# GET - LIST COURSES
# =========================================

@admin_course_bp.get("")
@roles_required("Administrator")
def list_courses():
    try:
        records = _service().list_courses()

        return jsonify(
            courses=records
        ), 200

    except Exception:
        logger.exception(
            "Failed to list courses."
        )

        return jsonify(
            error="Unable to load courses."
        ), 503


# =========================================
# GET - COURSE DETAILS
# =========================================

@admin_course_bp.get("/<course_id>")
@roles_required("Administrator")
def get_course(course_id):
    try:
        result = _service().get_course(
            course_id
        )

        if result is None:
            return jsonify(
                error="Course not found."
            ), 404

        return jsonify(
            course=result
        ), 200

    except ValueError as exc:
        return jsonify(
            error=str(exc)
        ), 400

    except Exception:
        logger.exception(
            "Failed to retrieve course."
        )

        return jsonify(
            error="Unable to load course."
        ), 503


# =========================================
# POST - CREATE COURSE
# =========================================

@admin_course_bp.post("")
@roles_required("Administrator")
def create_course():
    failure = _check_write()

    if failure is not None:
        return failure

    data, failure = _payload()

    if failure is not None:
        return failure

    try:
        course_id = _service().create_course(
            data
        )

        return jsonify(
            message="Course created successfully.",
            courseId=course_id,
        ), 201

    except ValueError as exc:
        return jsonify(
            error=str(exc)
        ), 400

    except CourseConflictError as exc:
        return jsonify(
            error=str(exc)
        ), 409

    except Exception:
        logger.exception(
            "Failed to create course."
        )

        return jsonify(
            error="Unable to create course."
        ), 503


# =========================================
# PUT - UPDATE COURSE
# =========================================

@admin_course_bp.put("/<course_id>")
@roles_required("Administrator")
def update_course(course_id):
    failure = _check_write()

    if failure is not None:
        return failure

    data, failure = _payload()

    if failure is not None:
        return failure

    try:
        updated_id = _service().update_course(
            course_id,
            data,
        )

        return jsonify(
            message="Course updated successfully.",
            courseId=updated_id,
        ), 200

    except ValueError as exc:
        return jsonify(
            error=str(exc)
        ), 400

    except CourseNotFoundError as exc:
        return jsonify(
            error=str(exc)
        ), 404

    except CourseConflictError as exc:
        return jsonify(
            error=str(exc)
        ), 409

    except Exception:
        logger.exception(
            "Failed to update course."
        )

        return jsonify(
            error="Unable to update course."
        ), 503


# =========================================
# DELETE - DELETE COURSE
# =========================================

@admin_course_bp.delete("/<course_id>")
@roles_required("Administrator")
def delete_course(course_id):
    failure = _check_write()

    if failure is not None:
        return failure

    try:
        _service().delete_course(
            course_id
        )

        return jsonify(
            message="Course deleted successfully."
        ), 200

    except ValueError as exc:
        return jsonify(
            error=str(exc)
        ), 400

    except CourseNotFoundError as exc:
        return jsonify(
            error=str(exc)
        ), 404

    except CourseConflictError as exc:
        return jsonify(
            error=str(exc)
        ), 409

    except Exception:
        logger.exception(
            "Failed to delete course."
        )

        return jsonify(
            error="Unable to delete course."
        ), 503
