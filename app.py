import secrets
from datetime import timedelta, timezone
from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    session,
)
from flask_caching import Cache
from utils import (
    users_collection,
    accounts_collection,
    transactions_collection,
    role_collection,
    status_collection,
    login_history_collection,
    counters_collection,
    generate_password,
    encode_password,
    send_admin_login_alert,
    send_customer_login_alert,
    track_login,
    send_monthly_report_to_superadmin,
    get_monthly_login_stats,
    create_accounts_for_customers,
    create_transaction,
    datetime,
    validate_user_data,
    validate_login_data,
    validate_transaction_data,
    require_admin,
    require_admin_or_employee,
    get_current_user,
    get_all_roles,
    get_all_statuses,
    get_role_name,
    get_status_name,
    generate_next_user_id,
    get_indian_states,
    get_cities_by_state,
    generate_transaction_chart,
)


# ----------------------------
# Flask app setup
# ----------------------------
app = Flask(__name__)
app.secret_key = secrets.token_urlsafe(32)
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=2)

# Initialize caching
cache = Cache(app, config={"CACHE_TYPE": "simple"})

# Run on startup to create accounts for any new customers
create_accounts_for_customers()


# ----------------------------
# Routes
# ----------------------------
@app.route("/")
def show_login_page():
    return render_template("login.html")


@app.route("/add_user", methods=["POST"])
@require_admin
def add_user(admin_user):
    user_data = request.get_json()
    if not user_data:
        return jsonify({"detail": "No data provided"}), 400

    # Auto-generate User ID
    user_data["UserId"] = generate_next_user_id()

    try:
        validate_user_data(user_data)
    except ValueError as e:
        return jsonify({"detail": str(e)}), 422

    # Check for existing user data (email only, since UserId is auto-generated)
    if users_collection.find_one({"EmailID": user_data.get("EmailID")}):
        return jsonify({"detail": "Email address already exists."}), 400

    # Check phone numbers
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
        # Clear cache when adding new user
        cache.delete("view//get_users")

        user_data["Password"] = generate_password(user_data["DOB"])
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

        # Create account for customers
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
                "LastTransaction": datetime.now(),
            }
            accounts_collection.insert_one(account_doc)

        return jsonify(
            {
                "message": "User added successfully",
                "UserId": user_data["UserId"],
                "GeneratedPassword": user_data["Password"],
            }
        )
    except Exception as e:
        return jsonify({"detail": f"Failed to create user: {str(e)}"}), 500


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    try:
        validate_login_data(data)
    except ValueError as e:
        return jsonify({"detail": str(e)}), 401

    # Find user without _id field to avoid serialization issues
    user = users_collection.find_one(
        {"UserId": data.get("UserId")}, {"_id": 0}  # Exclude _id field
    )
    if not user:
        return jsonify({"detail": "Invalid UserId or Password"}), 401

    dob_str = user["DOB"]
    expected_pw = f"Test@{datetime.strptime(dob_str, '%d-%m-%Y').strftime('%d%m%Y')}"
    if encode_password(data["Password"]) != encode_password(expected_pw):
        return jsonify({"detail": "Invalid UserId or Password"}), 401

    users_collection.update_one(
        {"UserId": data["UserId"]},
        {"$set": {"LastLoggedIn": datetime.now(timezone.utc).isoformat()}},
    )
    track_login(user["UserId"])

    # Handle email alerts safely
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


@app.route("/dashboard")
@get_current_user
def show_dashboard(current_user):
    return render_template("dashboard.html", user=current_user)


@app.route("/view_users")
@get_current_user
def show_users_page(current_user):
    return render_template("view_users.html", user=current_user)


@app.route("/add_user_page")
@require_admin
def show_add_user_page(admin_user):
    return render_template("add_user.html", user=admin_user)


@app.route("/get_users")
@get_current_user
def get_users(current_user):
    try:
        users = list(users_collection.find({}, {"_id": 0, "Password": 0}))

        # Calculate which users are actually active (logged in within last 3 months)
        three_months_ago = datetime.now(timezone.utc) - timedelta(days=90)
        recent_login_users = set()

        # Get users who logged in within last 3 months
        recent_logins = login_history_collection.find(
            {"LoginTime": {"$gte": three_months_ago.isoformat()}}, {"UserId": 1}
        )

        for login in recent_logins:
            recent_login_users.add(login["UserId"])

        # Add actual activity status to each user
        for user in users:
            user["DatabaseStatus"] = get_status_name(
                user.get("Status_ID", 1)
            )  # Original status from database

            # Determine actual activity status based on login history (simple Active/Inactive)
            if user["UserId"] in recent_login_users:
                user["ActivityStatus"] = "Active"
            else:
                user["ActivityStatus"] = "Inactive"

        return jsonify({"users": users})
    except Exception as e:
        print(f"Error in get_users: {e}")
        return jsonify({"detail": f"Failed to retrieve users: {str(e)}"}), 500


@app.route("/get_dashboard_stats")
@get_current_user
def get_dashboard_stats(current_user):
    try:
        # Get user statistics with better status handling
        total_users = users_collection.count_documents({})

        # Calculate active users based on login activity in last 3 months
        three_months_ago = datetime.now(timezone.utc) - timedelta(days=90)
        recent_login_users = set()

        # Get users who logged in within last 3 months
        recent_logins = login_history_collection.find(
            {"LoginTime": {"$gte": three_months_ago.isoformat()}}, {"UserId": 1}
        )

        for login in recent_logins:
            recent_login_users.add(login["UserId"])

        active_users = len(recent_login_users)

        # Get status-based counts for reference
        status_active_users = users_collection.count_documents({"Status_ID": 1})
        inactive_users = users_collection.count_documents({"Status_ID": 2})
        suspended_users = users_collection.count_documents({"Status_ID": 3})

        # Get role-based statistics
        customers = users_collection.count_documents({"Role": "Customer"})
        admins = users_collection.count_documents(
            {"Role": {"$in": ["Admin", "Super_Admin"]}}
        )
        employees = users_collection.count_documents({"Role": "Employee"})

        # Get recent login count (last 7 days)
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        recent_logins = login_history_collection.count_documents(
            {"LoginTime": {"$gte": week_ago.isoformat()}}
        )

        # Get total account balance (for admin view)
        total_balance = 0
        if current_user["Role"] in ["Admin", "Super_Admin"]:
            pipeline = [{"$group": {"_id": None, "total": {"$sum": "$Balance"}}}]
            result = list(accounts_collection.aggregate(pipeline))
            total_balance = result[0]["total"] if result else 0

        stats = {
            "total_users": total_users,
            "active_users": active_users,  # Users who logged in within last 3 months
            "inactive_users": inactive_users,
            "suspended_users": suspended_users,
            "status_active_users": status_active_users,  # Users with Status_ID = 1
            "customers": customers,
            "staff_members": admins + employees,
            "recent_logins": recent_logins,
            "total_balance": total_balance,
        }

        # Add customer-specific stats
        if current_user["Role"] == "Customer":
            account = accounts_collection.find_one({"UserId": current_user["UserId"]})
            stats["current_balance"] = account["Balance"] if account else 0

            # Get customer's transaction count this month
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


@app.route("/get_roles")
@get_current_user
def get_roles(current_user):
    """Get all available roles"""
    try:
        roles = get_all_roles()
        return jsonify({"roles": roles})
    except Exception as e:
        return jsonify({"detail": f"Failed to retrieve roles: {str(e)}"}), 500


@app.route("/get_statuses")
@get_current_user
def get_statuses(current_user):
    """Get all available statuses"""
    try:
        statuses = get_all_statuses()
        return jsonify({"statuses": statuses})
    except Exception as e:
        return jsonify({"detail": f"Failed to retrieve statuses: {str(e)}"}), 500


@app.route("/get_states")
@get_current_user
def get_states(current_user):
    """Get all Indian states"""
    try:
        states = get_indian_states()
        return jsonify({"states": states})
    except Exception as e:
        return jsonify({"detail": f"Failed to retrieve states: {str(e)}"}), 500


@app.route("/get_cities/<state>")
@get_current_user
def get_cities(current_user, state):
    """Get cities for a specific state"""
    try:
        cities = get_cities_by_state(state)
        return jsonify({"cities": cities})
    except Exception as e:
        return jsonify({"detail": f"Failed to retrieve cities: {str(e)}"}), 500


@app.route("/download_transaction_chart")
@get_current_user
def download_transaction_chart(current_user):
    """Generate and download transaction chart for current user"""
    try:
        if current_user["Role"] != "Customer":
            return (
                jsonify({"detail": "Only customers can download transaction charts"}),
                403,
            )

        chart_data = generate_transaction_chart(current_user["UserId"])
        if not chart_data:
            return (
                jsonify(
                    {"detail": "No transaction data available for chart generation"}
                ),
                404,
            )

        from flask import Response

        return Response(
            chart_data,
            mimetype="image/png",
            headers={
                "Content-Disposition": f'attachment; filename=transaction_chart_{current_user["UserId"]}.png'
            },
        )
    except Exception as e:
        return jsonify({"detail": f"Failed to generate chart: {str(e)}"}), 500


@app.route("/logout", methods=["POST"])
def logout():
    session.pop("user_id", None)
    return jsonify({"message": "Logged out successfully"})


@app.route("/check_auth")
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


@app.route("/monthly_report")
@require_admin
def get_monthly_report(current_user):
    if current_user["Role"] != "Super_Admin":
        return jsonify({"detail": "Super_Admin access required"}), 403
    stats = get_monthly_login_stats()
    if not stats:
        return jsonify({"detail": "Failed to generate monthly report"}), 500
    return jsonify(stats)


@app.route("/send_monthly_report", methods=["POST"])
@require_admin
def send_monthly_report_email(current_user):
    if current_user["Role"] != "Super_Admin":
        return jsonify({"detail": "Super_Admin access required"}), 403
    try:
        send_monthly_report_to_superadmin(current_user)
        return jsonify({"message": "Monthly report sent successfully to your email"})
    except Exception as e:
        return jsonify({"detail": f"Failed to send report: {str(e)}"}), 500


@app.route("/transaction_page")
@get_current_user
def show_transaction_page(current_user):
    if current_user["Role"] != "Customer":
        return jsonify({"detail": "Only customers can access this page."}), 403

    account = accounts_collection.find_one({"UserId": current_user["UserId"]})
    balance = account["Balance"] if account else 0
    return render_template("make_transaction.html", user=current_user, balance=balance)


@app.route("/make_transaction", methods=["POST"])
@get_current_user
def make_transaction(current_user):
    if current_user["Role"] != "Customer":
        return jsonify({"detail": "Only customers can make transactions."}), 403

    data = request.get_json()
    try:
        validate_transaction_data(data)
    except ValueError as e:
        return jsonify({"detail": str(e)}), 400

    if data.get("amount") <= 0:
        return jsonify({"detail": "Amount must be a positive number."}), 400

    account = accounts_collection.find_one({"UserId": current_user["UserId"]})
    if not account:
        return jsonify({"detail": "Account not found for this user."}), 404

    new_balance = account["Balance"]
    transaction_type = data.get("type", "").capitalize()

    if transaction_type == "Credit":
        new_balance += data["amount"]
    elif transaction_type == "Debit":
        if new_balance < data["amount"]:
            return jsonify({"detail": "Insufficient balance."}), 400
        new_balance -= data["amount"]
    else:
        return (
            jsonify(
                {"detail": "Invalid transaction type. Must be 'Credit' or 'Debit'."}
            ),
            400,
        )

    accounts_collection.update_one(
        {"_id": account["_id"]},
        {
            "$set": {
                "Balance": new_balance,
                "LastTransaction": datetime.now(timezone.utc),
            }
        },
    )
    create_transaction(
        current_user["UserId"], str(account["_id"]), data["amount"], transaction_type
    )

    return jsonify(
        {
            "message": f"{transaction_type} of {data['amount']} Rs. successful.",
            "new_balance": new_balance,
        }
    )


@app.route("/view_transactions_page")
@require_admin_or_employee
def show_transactions_page(current_user):
    return render_template("view_transactions.html", user=current_user)


@app.route("/get_transactions")
@require_admin_or_employee
@cache.cached(timeout=30)  # Cache for 30 seconds
def get_transactions(current_user):
    try:
        three_months_ago = datetime.now(timezone.utc) - timedelta(days=90)
        transactions = list(
            transactions_collection.find(
                {"TransactionDate": {"$gte": three_months_ago}},
                {"_id": 0},  # Exclude _id field to avoid conversion
            )
            .sort("TransactionDate", -1)
            .limit(1000)  # Limit results for performance
        )

        # Format dates more efficiently
        for txn in transactions:
            if isinstance(txn["TransactionDate"], datetime):
                txn["TransactionDate"] = txn["TransactionDate"].isoformat()

        return jsonify({"transactions": transactions})
    except Exception as e:
        return jsonify({"detail": f"Failed to retrieve transactions: {str(e)}"}), 500


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"detail": "Resource not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"detail": "Internal server error"}), 500


@app.errorhandler(403)
def forbidden(error):
    return jsonify({"detail": "Access forbidden"}), 403


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
