
"""Flask Application Factory - Student Management System Group 05."""

import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, request

from app.controllers.admin_student_controller import (
    admin_students_bp,
)
from app.controllers.auth_controller import auth_bp
from app.controllers.auth_security import LoginAttemptLimiter
from app.controllers.health_controller import health_bp
from app.controllers.student_profile_controller import (
    student_profile_bp,
)
from app.controllers.student_curriculum_controller import (
    student_curriculum_bp,
)

from app.controllers.student_transcript_controller import (
    student_transcript_bp,
)


from app.controllers.change_password_controller import (
    change_password_bp,
)


from app.controllers.lecturer_sections_controller import (
    lecturer_sections_bp,
)

from app.controllers.lecturer_profile_controller import lecturer_profile_bp
_BACKEND_ROOT = Path(__file__).resolve().parent.parent

from app.controllers.admin_lecturer_controller import (
    admin_lecturers_bp,
)
from app.controllers.admin_create_account_controller import (
    admin_create_account_bp,
)

from app.services.create_account_notification_service import (
    SMTPAccountNotifier,
)

from app.controllers.admin_assign_lecturer_controller import (
    admin_assign_lecturer_bp,
)
from app.controllers.admin_semester_controller import (
    admin_semester_bp,
)


from app.controllers.admin_faculty_controller import (
    admin_faculty_bp,
)

from app.controllers.admin_course_controller import (
    admin_course_bp,
)


from app.controllers.admin_class_section_controller import (
    admin_class_section_bp,
)

load_dotenv(
    dotenv_path=_BACKEND_ROOT / ".env",
    override=False,
)


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)

    if value is None or not value.strip():
        return default

    if value.strip().lower() in {"1", "true", "yes"}:
        return True

    if value.strip().lower() in {"0", "false", "no"}:
        return False

    raise RuntimeError(
        f"Invalid boolean configuration: {name}."
    )


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)

    app.config.update(
        SECRET_KEY=os.getenv("FLASK_SECRET_KEY", ""),
        AUTH_ALLOWED_ORIGIN=os.getenv(
            "AUTH_ALLOWED_ORIGIN",
            "http://localhost:5173",
        ),
        AUTH_COOKIE_SECURE=_env_bool(
            "AUTH_COOKIE_SECURE",
            False,
        ),
        AUTH_LOGIN_MAX_ATTEMPTS=10,
        AUTH_LOGIN_WINDOW_SECONDS=60,
        JSON_SORT_KEYS=False,
    )

    if test_config:
        app.config.update(test_config)

    if not app.config["SECRET_KEY"]:
        raise RuntimeError(
            "FLASK_SECRET_KEY must be set in backend/.env."
        )

    if not isinstance(
        app.config["AUTH_ALLOWED_ORIGIN"],
        str,
    ):
        raise RuntimeError(
            "AUTH_ALLOWED_ORIGIN must be a URL string."
        )
    app.register_blueprint(admin_create_account_bp)

    app.register_blueprint(admin_lecturers_bp)

    app.register_blueprint(
    admin_semester_bp,
    url_prefix="/api/admin/semesters",
    )

    app.register_blueprint(admin_assign_lecturer_bp)
    app.extensions["sms_login_limiter"] = LoginAttemptLimiter(
        limit=app.config["AUTH_LOGIN_MAX_ATTEMPTS"],
        window_seconds=app.config["AUTH_LOGIN_WINDOW_SECONDS"],
    )


    app.register_blueprint(
    admin_faculty_bp,
    url_prefix="/api/admin/faculties",
    )


    app.register_blueprint(
    admin_class_section_bp,
    url_prefix="/api/admin/class-sections",
    )

    # Health
    app.register_blueprint(
        health_bp,
        url_prefix="/api",
    )

    # Change Password - Student and Lecturer
    app.register_blueprint(
    change_password_bp,
    url_prefix="/api/auth",
    )

    # Authentication
    app.register_blueprint(
        auth_bp,
        url_prefix="/api/auth",
    )

    # Administrator
    app.register_blueprint(
        admin_students_bp,
        url_prefix="/api/admin",
    )

    # Student Profile
    app.register_blueprint(
        student_profile_bp,
        url_prefix="/api/student",
    )

    # Student Curriculum
    app.register_blueprint(
        student_curriculum_bp,
        url_prefix="/api/student",
    )

    # Student Academic Transcript
    app.register_blueprint(
    student_transcript_bp,
    url_prefix="/api/student",
    )


    app.register_blueprint(
    lecturer_sections_bp,
    url_prefix="/api/lecturer",
    )

    app.register_blueprint(
    admin_course_bp,
    url_prefix="/api/admin/courses",
)

        # Use Case 11 - Credential notification.
    # Disabled until a real SMTP provider is configured.
    if (
        not app.config.get("TESTING", False)
        and _env_bool("ACCOUNT_SMTP_ENABLED", False)
    ):
        app.extensions["sms_account_notifier"] = (
            SMTPAccountNotifier(
                host=os.getenv("ACCOUNT_SMTP_HOST", ""),
                port=int(
                    os.getenv("ACCOUNT_SMTP_PORT", "465")
                ),
                username=os.getenv(
                    "ACCOUNT_SMTP_USERNAME", ""
                ),
                password=os.getenv(
                    "ACCOUNT_SMTP_PASSWORD", ""
                ),
                sender=os.getenv(
                    "ACCOUNT_SMTP_FROM", ""
                ),
            )
        )
    app.register_blueprint(
    lecturer_profile_bp,
    url_prefix="/api/lecturer/profile",
    )
    @app.after_request
    def security_headers(response):
        response.headers.setdefault(
            "X-Content-Type-Options",
            "nosniff",
        )

        response.headers.setdefault(
            "Referrer-Policy",
            "no-referrer",
        )

        if request.path.startswith("/api/auth/"):
            response.headers["Cache-Control"] = "no-store"

        return response

    return app
