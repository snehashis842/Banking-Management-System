"""User creation (admin), user listing, and reference-data lookups."""
from datetime import datetime, timedelta, timezone
from flask import Blueprint, render_template, request, jsonify

from app.db import (
    users_collection,
    accounts_collection,
    login_history_collection,
    generate_next_user_id,
)
from app.security import generate_password, hash_password
from app.validators import validate_user_data
from app.email_utils import send_welcome_email, send_new_user_alert_to_superadmin
from app.auth import get_current_user, require_admin
from app.reference import get_all_roles, get_all_statuses, get_status_name
from app.locations import get_indian_states, get_cities_by_state
from app.extensions import cache

user_bp = Blueprint("user", __name__)


@user_bp.route("/add_user_page")
@require_admin
def show_add_user_page(admin_user):
    return render_template("add_user.html", user=admin_user)


@user_bp.route("/view_users")
@get_current_user
def show_users_page(current_user):
    return render_template("view_users.html", user=current_user)


@user_bp.route("/add_user", methods=["POST"])
@require_admin
def add_user(admin_user):
    user_data = request.get_json()
    if not user_data:
        return jsonify({"detail": "No data provided"}), 400

    user_data["UserId"] = generate_next_user_id()

    try:
        validate_user_data(user_data)
    except ValueError as e:
        return jsonify({"detail": str(e)}), 422

    if users_collection.find_one({"EmailID": user_data.get("EmailID")}):
        return jsonify({"detail": "Email address already exists."}), 400

    for phone in user_data.get("PhoneNo", []):
        existing_user = users_collection.find_one({"PhoneNo": phone})
        if existing_user:
            return (
                jsonify(
                    {
                        "detail": f"Phone number {phone} is already registered to user {existing_user['UserId']}."
                    }
                ),
                400,
            )

    try:
        cache.delete("view//get_users")

        raw_password = generate_password(user_data["DOB"])
        user_data["Password"] = hash_password(raw_password)
        user_data.update(
            {
                "AccessTokenIsLoggedIn": False,
                "CreatedBy": admin_user["UserId"],
                "CreatedOn": datetime.now(timezone.utc).isoformat(),
                "LastLoggedIn": None,
                "Status_ID": 1,
            }
        )

        users_collection.insert_one(user_data)

        if user_data["Role"] == "Customer":
            branch = (
                user_data.get("Address", "Unknown").strip().split()[0]
                if user_data.get("Address")
                else "Unknown"
            )
            account_doc = {
                "UserId": user_data["UserId"],
                "Balance": 0,
                "Branch": branch,
                "ActivityStatus": "Active",
                "LastTransaction": datetime.now(timezone.utc),
            }
            accounts_collection.insert_one(account_doc)

        try:
            send_welcome_email(user_data, raw_password)
            send_new_user_alert_to_superadmin(user_data)
        except Exception as e:
            print(f"New user notification email failed: {e}")

        return jsonify(
            {
                "message": "User added successfully",
                "UserId": user_data["UserId"],
                "GeneratedPassword": raw_password,
            }
        )
    except Exception as e:
        return jsonify({"detail": f"Failed to create user: {str(e)}"}), 500


@user_bp.route("/get_users")
@get_current_user
def get_users(current_user):
    try:
        users = list(users_collection.find({}, {"_id": 0, "Password": 0}))

        three_months_ago = datetime.now(timezone.utc) - timedelta(days=90)
        recent_login_users = set()

        recent_logins = login_history_collection.find(
            {"LoginTime": {"$gte": three_months_ago.isoformat()}}, {"UserId": 1}
        )
        for login in recent_logins:
            recent_login_users.add(login["UserId"])

        for user in users:
            user["DatabaseStatus"] = get_status_name(user.get("Status_ID", 1))
            user["ActivityStatus"] = (
                "Active" if user["UserId"] in recent_login_users else "Inactive"
            )

        return jsonify({"users": users})
    except Exception as e:
        print(f"Error in get_users: {e}")
        return jsonify({"detail": f"Failed to retrieve users: {str(e)}"}), 500


@user_bp.route("/get_roles")
@get_current_user
def get_roles(current_user):
    try:
        roles = get_all_roles()
        return jsonify({"roles": roles})
    except Exception as e:
        return jsonify({"detail": f"Failed to retrieve roles: {str(e)}"}), 500


@user_bp.route("/get_statuses")
@get_current_user
def get_statuses(current_user):
    try:
        statuses = get_all_statuses()
        return jsonify({"statuses": statuses})
    except Exception as e:
        return jsonify({"detail": f"Failed to retrieve statuses: {str(e)}"}), 500


@user_bp.route("/get_states")
@get_current_user
def get_states(current_user):
    try:
        states = get_indian_states()
        return jsonify({"states": states})
    except Exception as e:
        return jsonify({"detail": f"Failed to retrieve states: {str(e)}"}), 500


@user_bp.route("/get_cities/<state>")
@get_current_user
def get_cities(current_user, state):
    try:
        cities = get_cities_by_state(state)
        return jsonify({"cities": cities})
    except Exception as e:
        return jsonify({"detail": f"Failed to retrieve cities: {str(e)}"}), 500
