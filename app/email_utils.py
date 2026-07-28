"""All outbound email: welcome messages, admin alerts, monthly reports."""
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage
from app.config import Config
from app.db import users_collection, login_history_collection
from app.charts import generate_transaction_chart

SMTP_EMAIL = Config.SMTP_EMAIL
SMTP_PASSWORD = Config.SMTP_PASSWORD
SMTP_HOST = Config.SMTP_HOST
SMTP_PORT = Config.SMTP_PORT
ADMIN_EMAILS = Config.ADMIN_EMAILS


def _send(msg):
    """Shared SMTP send helper — one place to change host/port/auth."""
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.login(SMTP_EMAIL, SMTP_PASSWORD)
        smtp.send_message(msg)


def send_welcome_email(user, raw_password):
    """Send a new user their UserId and password by email.
    raw_password must be the PLAINTEXT password (before hashing) — call this
    immediately after creating the account, never after the hash is all
    that's left in memory."""
    msg = EmailMessage()
    msg["Subject"] = "Welcome — Your Bank Account Details"
    msg["From"] = SMTP_EMAIL
    msg["To"] = user["EmailID"]
    msg.set_content(
        f"""
Hello {user['First_Name']} {user['Last_Name']},

Your account has been created successfully.

  User ID:  {user['UserId']}
  Password: {raw_password}

Please keep these credentials safe, and change your password after your
first login.

Thank you for banking with us.
"""
    )
    try:
        _send(msg)
    except Exception as e:
        print("Welcome email failed:", e)


def send_new_user_alert_to_superadmin(user):
    """Notify super admins whenever a new user account is created,
    whether via self-signup or admin creation."""
    msg = EmailMessage()
    msg["Subject"] = f"New User Registered: {user['First_Name']} {user['Last_Name']}"
    msg["From"] = SMTP_EMAIL
    msg["To"] = ", ".join(ADMIN_EMAILS)
    msg.set_content(
        f"""
A new user account was just created.

  User ID:    {user['UserId']}
  Name:       {user['First_Name']} {user['Last_Name']}
  Email:      {user['EmailID']}
  Role:       {user['Role']}
  Created By: {user.get('CreatedBy', 'unknown')}
  Time:       {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
"""
    )
    try:
        _send(msg)
    except Exception as e:
        print("New user alert email failed:", e)


def send_admin_login_alert(user):
    """Sends a login alert to the admin."""
    msg = EmailMessage()
    msg["Subject"] = f"User Logged In: {user['First_Name']} {user['Last_Name']}"
    msg["From"] = SMTP_EMAIL
    msg["To"] = ", ".join(ADMIN_EMAILS)
    msg.set_content(
        f"""
User {user['First_Name']} {user['Last_Name']} (UserId: {user['UserId']}) just logged in.
Role: {user['Role']}
Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
"""
    )
    try:
        _send(msg)
    except Exception as e:
        print("Admin email failed:", e)



def send_customer_login_alert(user):
    """Sends a login alert to the customer with transaction chart."""
    try:
        msg = EmailMessage()
        msg["Subject"] = "Successful Login Notification - Transaction Summary"
        msg["From"] = SMTP_EMAIL
        msg["To"] = user["EmailID"]

        # Generate transaction chart
        chart_data = generate_transaction_chart(user["UserId"])

        if chart_data:
            email_content = f"""
Dear {user['First_Name']},

This is to confirm that your account was successfully logged into at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}.

We've attached your transaction summary chart for the last 6 months for your reference.

If this login was not you, please contact support immediately.

Thank you,
Your Bank Team
"""
            msg.set_content(email_content)

            # Attach the chart
            msg.add_attachment(
                chart_data,
                maintype="image",
                subtype="png",
                filename=f'transaction_summary_{user["UserId"]}.png',
            )
        else:
            # Fallback to simple email if chart generation fails
            email_content = f"""
Dear {user['First_Name']},

This is to confirm that your account was successfully logged into at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}.

If this was not you, please contact support immediately.

Thank you,
Your Bank Team
"""
            msg.set_content(email_content)

        _send(msg)

        print(f"Login alert with transaction chart sent to {user['EmailID']}")

    except Exception as e:
        print(f"Customer email failed for {user['EmailID']}: {e}")


def track_login(user_id):
    """Track user login in history collection"""
    try:
        now = datetime.now(timezone.utc)
        login_record = {
            "UserId": user_id,
            "LoginTime": now.isoformat(),
            "Month": now.strftime("%Y-%m"),
            "Date": now.strftime("%Y-%m-%d"),
        }
        login_history_collection.insert_one(login_record)
    except Exception as e:
        print(f"Failed to track login: {e}")



def get_monthly_login_stats():
    """Get login statistics for current month"""
    try:
        now = datetime.now(timezone.utc)
        current_month = now.strftime("%Y-%m")
        all_users = list(users_collection.find({}, {"_id": 0}))
        login_stats = []
        total_logins = 0

        for user in all_users:
            login_count = login_history_collection.count_documents(
                {"UserId": user["UserId"], "Month": current_month}
            )
            last_login_record = login_history_collection.find_one(
                {"UserId": user["UserId"]}, sort=[("LoginTime", -1)]
            )
            last_login = (
                last_login_record["LoginTime"]
                if last_login_record
                else user.get("LastLoggedIn", "Never")
            )

            login_stats.append(
                {
                    "UserId": user["UserId"],
                    "Name": f"{user['First_Name']} {user['Last_Name']}",
                    "Role": user["Role"],
                    "LoginCount": login_count,
                    "LastLogin": last_login,
                }
            )
            total_logins += login_count

        login_stats.sort(key=lambda x: x["LoginCount"], reverse=True)

        return {
            "month": now.strftime("%B %Y"),
            "total_users": len(all_users),
            "total_logins": total_logins,
            "active_users": len([u for u in login_stats if u["LoginCount"] > 0]),
            "user_stats": login_stats,
        }
    except Exception as e:
        print(f"Error getting monthly stats: {e}")
        return None


def send_monthly_report_to_superadmin(superadmin_user):
    """Send monthly login report to Super_Admin"""
    try:
        stats = get_monthly_login_stats()
        if not stats:
            return

        email_content = f"""Monthly Login Report - {stats['month']}

SUMMARY
Total Users: {stats['total_users']}
Active Users: {stats['active_users']}
Total Logins: {stats['total_logins']}

USER ACTIVITY
"""
        for user_stat in stats["user_stats"]:
            status = "Active" if user_stat["LoginCount"] > 0 else "Inactive"
            email_content += (
                f"{user_stat['Name']} ({user_stat['UserId']}) - {user_stat['Role']}\n"
            )
            email_content += f"  Logins this month: {user_stat['LoginCount']}\n"
            email_content += f"  Status: {status}\n\n"

        email_content += f"Report generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        email_content += f"Triggered by: {superadmin_user['First_Name']} {superadmin_user['Last_Name']}"

        msg = EmailMessage()
        msg["Subject"] = f"Monthly User Activity Report - {stats['month']}"
        msg["From"] = SMTP_EMAIL
        msg["To"] = ", ".join(ADMIN_EMAILS)
        msg.set_content(email_content)

        _send(msg)
        print(f"Monthly report sent to admin emails: {', '.join(ADMIN_EMAILS)}")
    except Exception as e:
        print(f"Failed to send monthly report: {e}")


