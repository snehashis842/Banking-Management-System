"""Route decorators for authentication and role-based authorization."""
from functools import wraps
from flask import jsonify, redirect, session, url_for
from app.db import users_collection


def get_current_user(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"detail": "Not authenticated"}), 401

        # Use projection to only fetch needed fields for better performance
        user = users_collection.find_one(
            {"UserId": user_id},
            {"_id": 0, "Password": 0},  # Exclude _id and password fields
        )
        if not user:
            session.pop("user_id", None)
            return jsonify({"detail": "User not found"}), 401
        return f(*args, **kwargs, current_user=user)

    return decorated_function


def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            return redirect(url_for("show_login_page"))

        user = users_collection.find_one(
            {"UserId": user_id},
            {"_id": 0, "Password": 0},  # Exclude _id and password fields
        )
        if not user or user["Role"] not in ["Admin", "Super_Admin"]:
            return jsonify({"detail": "Admin access required"}), 403
        return f(*args, **kwargs, admin_user=user)

    return decorated_function


def require_admin_or_employee(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"detail": "Not authenticated"}), 401

        user = users_collection.find_one(
            {"UserId": user_id},
            {"_id": 0, "Password": 0},  # Exclude _id and password fields
        )
        if not user or user["Role"] not in ["Admin", "Super_Admin", "Employee"]:
            return jsonify({"detail": "Admin or Employee access required"}), 403
        return f(*args, **kwargs, current_user=user)

    return decorated_function


# ----------------------------
# Reference Data Helpers
