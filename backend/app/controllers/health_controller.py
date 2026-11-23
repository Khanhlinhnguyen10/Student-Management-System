
from flask import Blueprint, jsonify


# Blueprint dành cho Health Check API
health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health_check():
    return jsonify({
        "status": "ok",
        "message": "Student Management System API is running"
    }), 200
