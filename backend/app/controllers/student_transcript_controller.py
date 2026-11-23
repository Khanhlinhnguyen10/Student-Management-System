
"""Student Academic Transcript HTTP Controller.

Group 05 - Use Case: View Academic Transcript.

Responsibilities:
- Accept GET /api/student/transcript.
- Require authenticated Student role.
- Get userId from the verified SQL-backed session.
- Delegate business logic to StudentTranscriptService.
- Return JSON without exposing internal database errors.
"""

import logging

from flask import (
    Blueprint,
    current_app,
    g,
    jsonify,
)

from app.controllers.auth_security import (
    roles_required,
)

from app.services.student_transcript_service import (
    StudentTranscriptNotFoundError,
    StudentTranscriptService,
)


student_transcript_bp = Blueprint(
    "student_transcript",
    __name__,
)

logger = logging.getLogger(__name__)


# =============================================
# SERVICE ACCESS
# =============================================

def _service() -> StudentTranscriptService:
    """Allow test injection; use real service by default."""
    return (
        current_app.extensions.get(
            "sms_student_transcript_service"
        )
        or StudentTranscriptService()
    )


# =============================================
# RESPONSE CACHE PROTECTION
# =============================================

@student_transcript_bp.after_request
def prevent_transcript_caching(response):
    """Prevent browser/proxy caching of academic records."""
    response.headers["Cache-Control"] = "no-store"
    return response


# =============================================
# VIEW STUDENT TRANSCRIPT
# =============================================

@student_transcript_bp.get("/transcript")
@roles_required("Student")
def view_transcript():
    """
    GET /api/student/transcript

    Access:
        Authenticated Student only.

    Student identity:
        Retrieved from the verified session,
        never from user-supplied query parameters.

    Successful response:
        {
            "transcript": {
                "studentId": "...",
                "hasFinalizedGrades": true,
                "totalFinalizedResults": 2,
                "latestCumulativeGPA": 3.75,
                "semesters": [...]
            }
        }
    """
    try:
        user_id = g.auth_principal.user_id

        transcript = _service().view_transcript(
            user_id
        )

        return jsonify(
            transcript=transcript
        ), 200

    except StudentTranscriptNotFoundError:
        return jsonify(
            error="Student record not found."
        ), 404

    except ValueError:
        return jsonify(
            error="Invalid student session context."
        ), 400

    except Exception:
        logger.exception(
            "Failed to retrieve student transcript."
        )

        return jsonify(
            error="Unable to retrieve transcript at this time."
        ), 503
