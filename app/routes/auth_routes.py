"""Login, signup, logout, and session-check routes."""
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, jsonify, session

from app.db import users_collection, accounts_collection, generate_next_user_id
from app.security import generate_password, hash_password, verify_password
from app.validators import validate_signup_data, validate_login_data
from app.email_utils import (
    send_welcome_email,
    send_new_user_alert_to_superadmin,
    send_admin_login_alert,
    send_customer_login_alert,
    send_monthly_report_to_superadmin,
    track_login,
)
from app.auth import get_current_user
from app.extensions import cache

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def show_login_page():
    return render_template("login.html")


@auth_bp.route("/signup_page")
def show_signup_page():
    return render_template("signup.html")


@auth_bp.route("/signup", methods=["POST"])
def signup():
    """Public self-signup. Always creates a Customer account — Admin,
    Employee, and Super_Admin accounts must still be created by an admin
    via /add_user. Password is always the DOB-derived default
    (Test@DDMMYYYY), emailed to the user — not chosen at signup."""
    data = request.get_json()
    if not data:
        return jsonify({"detail": "No data provided"}), 400

    try:
        validate_signup_data(data)
    except ValueError as e:
        return jsonify({"detail": str(e)}), 422

    if users_collection.find_one({"EmailID": data.get("EmailID")}):
        return jsonify({"detail": "Email address already exists."}), 400

    for phone in data.get("PhoneNo", []):
        if users_collection.find_one({"PhoneNo": phone}):
            return (
                jsonify({"detail": f"Phone number {phone} is already registered."}),
                400,
            )

    try:
        raw_password = generate_password(data["DOB"])
        user_data = {
            "UserId": generate_next_user_id(),
            "First_Name": data["First_Name"],
            "Last_Name": data["Last_Name"],
            "EmailID": data["EmailID"],
            "DOB": data["DOB"],
            "PhoneNo": data["PhoneNo"],
            "Gender": data["Gender"],
            "Address": data["Address"],
            "Role": "Customer",
            "Password": hash_password(raw_password),
            "AccessTokenIsLoggedIn": False,
            "CreatedBy": "self-signup",
            "CreatedOn": datetime.now(timezone.utc).isoformat(),
            "LastLoggedIn": None,
            "Status_ID": 1,
        }
        users_collection.insert_one(user_data)

        branch = (
            user_data["Address"].strip().split()[0]
            if user_data.get("Address")
            else "Unknown"
        )
        accounts_collection.insert_one(
            {
                "UserId": user_data["UserId"],
                "Balance": 0,
                "Branch": branch,
                "ActivityStatus": "Active",
                "LastTransaction": datetime.now(timezone.utc),
            }
        )

        cache.delete("view//get_users")

        try:
            send_welcome_email(user_data, raw_password)
            send_new_user_alert_to_superadmin(user_data)
        except Exception as e:
            print(f"Signup notification email failed: {e}")

        return jsonify(
            {
                "message": "Account created successfully! You can now log in.",
                "UserId": user_data["UserId"],
            }
        )
    except Exception as e:
        return jsonify({"detail": f"Failed to create account: {str(e)}"}), 500


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"detail": "No data provided"}), 400

    try:
        validate_login_data(data)
    except ValueError as e:
        return jsonify({"detail": str(e)}), 401

    user = users_collection.find_one({"UserId": data.get("UserId")}, {"_id": 0})
    if not user or not verify_password(data["Password"], user.get("Password", "")):
        return jsonify({"detail": "Invalid UserId or Password"}), 401

    users_collection.update_one(
        {"UserId": data["UserId"]},
        {"$set": {"LastLoggedIn": datetime.now(timezone.utc).isoformat()}},
    )
    track_login(user["UserId"])

    try:
        send_admin_login_alert(user)
        if user["Role"] == "Customer":
            send_customer_login_alert(user)
        if user["Role"] == "Super_Admin":
            send_monthly_report_to_superadmin(user)
    except Exception as e:
        print(f"Email notification failed: {e}")

    session["user_id"] = user["UserId"]
    return jsonify(
        {
            "message": f"Login successful! Welcome {user['First_Name']} {user['Last_Name']}",
            "role": user["Role"],
        }
    )


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.pop("user_id", None)
    return jsonify({"message": "Logged out successfully"})


@auth_bp.route("/check_auth")
@get_current_user
def check_auth(current_user):
    return jsonify(
        {
            "authenticated": True,
            "user": {
                "UserId": current_user["UserId"],
                "First_Name": current_user["First_Name"],
                "Last_Name": current_user["Last_Name"],
                "Role": current_user["Role"],
            },
        }
    )
