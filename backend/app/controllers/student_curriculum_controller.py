
"""Student View Curriculum HTTP API."""

import logging

from flask import (
    Blueprint,
    current_app,
    g,
    jsonify,
)

from app.controllers.auth_security import roles_required

from app.services.student_curriculum_service import (
    StudentCurriculumAmbiguousError,
    StudentCurriculumNotFoundError,
    StudentCurriculumService,
)


student_curriculum_bp = Blueprint(
    "student_curriculum",
    __name__,
)

logger = logging.getLogger(__name__)


def _service() -> StudentCurriculumService:
    return (
        current_app.extensions.get(
            "sms_student_curriculum_service"
        )
        or StudentCurriculumService()
    )


@student_curriculum_bp.after_request
def disable_curriculum_cache(response):
    response.headers["Cache-Control"] = "no-store"
    return response


@student_curriculum_bp.get("/curriculum")
@roles_required("Student")
def view_curriculum():
    try:
        # userId comes from verified SQL-backed session.
        user_id = g.auth_principal.user_id

        curriculum = _service().view_curriculum(
            user_id
        )

        return jsonify(curriculum=curriculum), 200

    except StudentCurriculumNotFoundError as exc:
        return jsonify(error=str(exc)), 404

    except StudentCurriculumAmbiguousError as exc:
        return jsonify(error=str(exc)), 409

    except ValueError:
        return jsonify(
            error="Invalid student context."
        ), 400

    except Exception:
        logger.exception(
            "Student curriculum retrieval failed."
        )

        return jsonify(
            error="Cannot retrieve curriculum at this time."
        ), 503
