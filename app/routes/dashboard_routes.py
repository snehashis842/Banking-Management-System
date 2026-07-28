"""Dashboard stats and the monthly Super_Admin report."""
from datetime import datetime, timedelta, timezone
from flask import Blueprint, render_template, jsonify

from app.db import (
    users_collection,
    accounts_collection,
    transactions_collection,
    login_history_collection,
)
from app.auth import get_current_user, require_admin
from app.email_utils import get_monthly_login_stats, send_monthly_report_to_superadmin

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@get_current_user
def show_dashboard(current_user):
    return render_template("dashboard.html", user=current_user)


@dashboard_bp.route("/get_dashboard_stats")
@get_current_user
def get_dashboard_stats(current_user):
    try:
        total_users = users_collection.count_documents({})

        three_months_ago = datetime.now(timezone.utc) - timedelta(days=90)
        recent_login_users = set()
        recent_logins = login_history_collection.find(
            {"LoginTime": {"$gte": three_months_ago.isoformat()}}, {"UserId": 1}
        )
        for login in recent_logins:
            recent_login_users.add(login["UserId"])
        active_users = len(recent_login_users)

        status_active_users = users_collection.count_documents({"Status_ID": 1})
        inactive_users = users_collection.count_documents({"Status_ID": 2})
        suspended_users = users_collection.count_documents({"Status_ID": 3})

        customers = users_collection.count_documents({"Role": "Customer"})
        admins = users_collection.count_documents(
            {"Role": {"$in": ["Admin", "Super_Admin"]}}
        )
        employees = users_collection.count_documents({"Role": "Employee"})

        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        recent_logins_count = login_history_collection.count_documents(
            {"LoginTime": {"$gte": week_ago.isoformat()}}
        )

        total_balance = 0
        if current_user["Role"] in ["Admin", "Super_Admin"]:
            pipeline = [{"$group": {"_id": None, "total": {"$sum": "$Balance"}}}]
            result = list(accounts_collection.aggregate(pipeline))
            total_balance = result[0]["total"] if result else 0

        stats = {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": inactive_users,
            "suspended_users": suspended_users,
            "status_active_users": status_active_users,
            "customers": customers,
            "staff_members": admins + employees,
            "recent_logins": recent_logins_count,
            "total_balance": total_balance,
        }

        if current_user["Role"] == "Customer":
            account = accounts_collection.find_one({"UserId": current_user["UserId"]})
            stats["current_balance"] = account["Balance"] if account else 0

            current_month = datetime.now(timezone.utc).replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )
            monthly_transactions = transactions_collection.count_documents(
                {
                    "UserId": current_user["UserId"],
                    "TransactionDate": {"$gte": current_month},
                }
            )
            stats["monthly_transactions"] = monthly_transactions

        return jsonify(stats)
    except Exception as e:
        print(f"Error in get_dashboard_stats: {e}")
        return jsonify({"detail": f"Failed to retrieve statistics: {str(e)}"}), 500


@dashboard_bp.route("/monthly_report")
@require_admin
def get_monthly_report(current_user):
    if current_user["Role"] != "Super_Admin":
        return jsonify({"detail": "Super_Admin access required"}), 403
    stats = get_monthly_login_stats()
    if not stats:
        return jsonify({"detail": "Failed to generate monthly report"}), 500
    return jsonify(stats)


@dashboard_bp.route("/send_monthly_report", methods=["POST"])
@require_admin
def send_monthly_report_email(current_user):
    if current_user["Role"] != "Super_Admin":
        return jsonify({"detail": "Super_Admin access required"}), 403
    try:
        send_monthly_report_to_superadmin(current_user)
        return jsonify({"message": "Monthly report sent successfully to your email"})
    except Exception as e:
        return jsonify({"detail": f"Failed to send report: {str(e)}"}), 500
