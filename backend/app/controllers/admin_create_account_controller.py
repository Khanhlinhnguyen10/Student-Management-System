
"""Administrator Create Account Controller - Group 05.

Requirement: Use Case 11 - Create Account.

Endpoints:
    GET  /api/admin/create-account/faculties
    GET  /api/admin/create-account/majors
    POST /api/admin/create-account

Only authenticated Administrators can use these APIs.
"""

import logging

from flask import Blueprint, current_app, jsonify, request

from app.controllers.auth_security import (
    SESSION_COOKIE_NAME,
    request_has_approved_origin,
    roles_required,
    validate_csrf,
)

from app.repositories.create_account_repository import (
    AccountAlreadyExistsError,
    AccountIdGenerationError,
    AccountReferenceError,
)

from app.services.create_account_service import (
    CreateAccountService,
    CreateAccountValidationError,
)


logger = logging.getLogger(__name__)

admin_create_account_bp = Blueprint(
    "admin_create_account",
    __name__,
    url_prefix="/api/admin/create-account",
)


def _get_service() -> CreateAccountService:
    """Allow mocked Service injection in unit tests."""

    return (
        current_app.extensions.get(
            "sms_create_account_service"
        )
        or CreateAccountService()
    )


def _get_notifier():
    """Credential delivery dependency for Use Case 11.

    No delivery provider is configured at this stage.
    A missing provider MUST block account creation.
    """

    return current_app.extensions.get(
        "sms_account_notifier"
    )


@admin_create_account_bp.after_request
def disable_cache(response):
    """Do not cache account-related responses."""

    response.headers["Cache-Control"] = "no-store"
    return response


# =========================================
# GET FACULTIES
# =========================================

@admin_create_account_bp.get("/faculties")
@roles_required("Administrator")
def list_faculties():
    """Faculty options for Lecturer account creation."""

    try:
        faculties = _get_service().list_faculties()

        return jsonify(
            faculties=faculties,
        ), 200

    except Exception:
        logger.error(
            "Create Account: failed to load faculties."
        )

        return jsonify(
            error="Unable to load faculties."
        ), 503


# =========================================
# GET MAJORS
# =========================================

@admin_create_account_bp.get("/majors")
@roles_required("Administrator")
def list_majors():
    """Major options for Student account creation."""

    try:
        majors = _get_service().list_majors()

        return jsonify(
            majors=majors,
        ), 200

    except Exception:
        logger.error(
            "Create Account: failed to load majors."
        )

        return jsonify(
            error="Unable to load majors."
        ), 503


# =========================================
# POST CREATE ACCOUNT
# =========================================

@admin_create_account_bp.post("")
@roles_required("Administrator")
def create_account():
    """Create an account only when delivery is configured."""

    # -------------------------------------
    # 1. Origin verification
    # -------------------------------------

    if not request_has_approved_origin():
        return jsonify(
            error="Request origin not allowed."
        ), 403

    # -------------------------------------
    # 2. CSRF verification
    # -------------------------------------

    raw_session_token = request.cookies.get(
        SESSION_COOKIE_NAME
    )

    if (
        not raw_session_token
        or not validate_csrf(raw_session_token)
    ):
        return jsonify(
            error="Invalid CSRF token."
        ), 403

    # -------------------------------------
    # 3. JSON verification
    # -------------------------------------

    if not request.is_json:
        return jsonify(
            error="JSON request required."
        ), 415

    if (
        request.content_length is not None
        and request.content_length > 8192
    ):
        return jsonify(
            error="Request payload too large."
        ), 413

    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        return jsonify(
            error="Invalid account data."
        ), 400

    # -------------------------------------
    # 4. Delivery prerequisite
    # -------------------------------------

    notifier = _get_notifier()

    if notifier is None:
        return jsonify(
            error=(
                "Account creation is not yet available "
                "because credential delivery "
                "is not configured."
            )
        ), 503

    # The provider must implement deliver().
    delivery_method = getattr(
        notifier,
        "deliver",
        None,
    )

    if not callable(delivery_method):
        logger.error(
            "Create Account: invalid notifier configuration."
        )

        return jsonify(
            error="Account delivery configuration is invalid."
        ), 503

    # -------------------------------------
    # 5. Service validation + SQL commit
    # -------------------------------------

    try:
        result = _get_service().create_record(
            payload
        )

    except CreateAccountValidationError as exc:
        return jsonify(
            error=str(exc)
        ), 400

    except AccountAlreadyExistsError as exc:
        return jsonify(
            error=str(exc)
        ), 409

    except AccountReferenceError as exc:
        return jsonify(
            error=str(exc)
        ), 400

    except AccountIdGenerationError:
        return jsonify(
            error="Unable to generate account ID."
        ), 503

    except Exception:
        logger.error(
            "Create Account: database operation failed."
        )

        return jsonify(
            error="Unable to create account."
        ), 503

    # -------------------------------------
    # 6. Deliver initial credentials
    # -------------------------------------
    # This happens AFTER the DB commit.
    # Never return the initial password in JSON.

    try:
        delivery_method(
            account=result["account"],
            credentials=result["initialCredentials"],
            email=payload.get("email"),
            phone_number=payload.get("phoneNumber"),
        )

    except Exception:
        logger.error(
            "Create Account: credential delivery failed."
        )

        # Important: the database COMMIT already happened.
        # Never claim the transaction was rolled back.
        return jsonify(
            error=(
                "Account was created, but credential "
                "delivery failed. Do not create "
                "the same account again."
            ),
            account=result["account"],
        ), 502

    # -------------------------------------
    # 7. Success
    # -------------------------------------

    return jsonify(
        message="Account created successfully.",
        account=result["account"],
    ), 201
