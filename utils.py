import base64
import re
import smtplib
import uuid
import io
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from functools import wraps
from typing import List, Optional
from flask import jsonify, redirect, session, url_for
from pymongo import MongoClient
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from collections import defaultdict


# ----------------------------
# MongoDB Connection with Connection Pooling
# ----------------------------
client = MongoClient(
    "mongodb://localhost:27017/",
    maxPoolSize=50,
    minPoolSize=10,
    maxIdleTimeMS=30000,
    waitQueueTimeoutMS=5000,
)
db = client["project"]
users_collection = db["users"]
login_history_collection = db["login_history"]
accounts_collection = db["accounts"]
transactions_collection = db["transactions"]
role_collection = db["role"]
status_collection = db["status"]
counters_collection = db["counters"]  # For auto-incrementing User IDs


# Create indexes for better performance
def create_indexes():
    """Create database indexes for better query performance"""
    try:
        users_collection.create_index("UserId", unique=True)
        users_collection.create_index("EmailID", unique=True)
        users_collection.create_index("Role")
        users_collection.create_index("Status_ID")
        login_history_collection.create_index([("UserId", 1), ("Month", 1)])
        accounts_collection.create_index("UserId", unique=True)
        transactions_collection.create_index([("UserId", 1), ("TransactionDate", -1)])
        role_collection.create_index("role_id", unique=True)
        status_collection.create_index("status_id", unique=True)
        print("Database indexes created successfully")
    except Exception as e:
        print(f"Index creation warning: {e}")


# Initialize reference data
def initialize_reference_data():
    """Initialize role and status collections with default data"""
    try:
        # Clean up any invalid documents first
        role_collection.delete_many({"role_id": None})
        status_collection.delete_many({"status_id": None})

        # Initialize roles if not exists
        if role_collection.count_documents({}) == 0:
            roles = [
                {
                    "role_id": 1,
                    "role_name": "Super_Admin",
                    "description": "Super Administrator with full access",
                },
                {
                    "role_id": 2,
                    "role_name": "Admin",
                    "description": "Administrator with management access",
                },
                {
                    "role_id": 3,
                    "role_name": "Employee",
                    "description": "Employee with limited access",
                },
                {
                    "role_id": 4,
                    "role_name": "Customer",
                    "description": "Customer with account access",
                },
            ]
            role_collection.insert_many(roles)
            print("Role collection initialized")

        # Initialize statuses if not exists
        if status_collection.count_documents({}) == 0:
            statuses = [
                {
                    "status_id": 1,
                    "status_name": "Active",
                    "description": "User is active",
                },
                {
                    "status_id": 2,
                    "status_name": "Inactive",
                    "description": "User is inactive",
                },
                {
                    "status_id": 3,
                    "status_name": "Suspended",
                    "description": "User is suspended",
                },
                {
                    "status_id": 4,
                    "status_name": "Pending",
                    "description": "User registration pending",
                },
            ]
            status_collection.insert_many(statuses)
            print("Status collection initialized")

    except Exception as e:
        print(f"Reference data initialization warning: {e}")


# Initialize indexes and reference data
create_indexes()
initialize_reference_data()


# ----------------------------
# Auto User ID Generation
# ----------------------------
def generate_next_user_id():
    """Generate the next sequential User ID based on existing numeric format"""
    try:
        # Initialize counter if it doesn't exist
        counter_doc = counters_collection.find_one({"_id": "user_id"})
        if not counter_doc:
            # Find the highest existing numeric User ID to start from
            existing_users = list(users_collection.find({}, {"UserId": 1}))
            max_id = 56125810020  # Default starting point if no users exist

            for user in existing_users:
                user_id = user.get("UserId", "")
                # Check if it's a numeric User ID
                if user_id.isdigit():
                    current_num = int(user_id)
                    max_id = max(max_id, current_num)

            # Initialize counter starting from max_id
            counters_collection.insert_one({"_id": "user_id", "sequence": max_id})
            counter_doc = {"sequence": max_id}

        # Increment and get next ID
        result = counters_collection.find_one_and_update(
            {"_id": "user_id"}, {"$inc": {"sequence": 1}}, return_document=True
        )

        next_number = result["sequence"]
        return str(
            next_number
        )  # Return as string (e.g., "56125810021", "56125810022", etc.)

    except Exception as e:
        print(f"Error generating User ID: {e}")
        # Fallback to timestamp-based ID
        import time

        return str(int(time.time()))


# ----------------------------
# Indian States and Cities Data
# ----------------------------
INDIAN_STATES_CITIES = {
    "Andhra Pradesh": [
        "Visakhapatnam",
        "Vijayawada",
        "Guntur",
        "Nellore",
        "Kurnool",
        "Rajahmundry",
        "Tirupati",
        "Kadapa",
        "Anantapur",
        "Eluru",
    ],
    "Arunachal Pradesh": [
        "Itanagar",
        "Naharlagun",
        "Pasighat",
        "Tezpur",
        "Bomdila",
        "Ziro",
        "Along",
        "Tezu",
        "Changlang",
        "Khonsa",
    ],
    "Assam": [
        "Guwahati",
        "Silchar",
        "Dibrugarh",
        "Jorhat",
        "Nagaon",
        "Tinsukia",
        "Tezpur",
        "Bongaigaon",
        "Karimganj",
        "Sivasagar",
    ],
    "Bihar": [
        "Patna",
        "Gaya",
        "Bhagalpur",
        "Muzaffarpur",
        "Purnia",
        "Darbhanga",
        "Bihar Sharif",
        "Arrah",
        "Begusarai",
        "Katihar",
    ],
    "Chhattisgarh": [
        "Raipur",
        "Bhilai",
        "Korba",
        "Bilaspur",
        "Durg",
        "Rajnandgaon",
        "Jagdalpur",
        "Raigarh",
        "Ambikapur",
        "Mahasamund",
    ],
    "Goa": [
        "Panaji",
        "Vasco da Gama",
        "Margao",
        "Mapusa",
        "Ponda",
        "Bicholim",
        "Curchorem",
        "Sanquelim",
        "Valpoi",
        "Pernem",
    ],
    "Gujarat": [
        "Ahmedabad",
        "Surat",
        "Vadodara",
        "Rajkot",
        "Bhavnagar",
        "Jamnagar",
        "Junagadh",
        "Gandhinagar",
        "Anand",
        "Navsari",
    ],
    "Haryana": [
        "Faridabad",
        "Gurgaon",
        "Panipat",
        "Ambala",
        "Yamunanagar",
        "Rohtak",
        "Hisar",
        "Karnal",
        "Sonipat",
        "Panchkula",
    ],
    "Himachal Pradesh": [
        "Shimla",
        "Dharamshala",
        "Solan",
        "Mandi",
        "Palampur",
        "Baddi",
        "Nahan",
        "Paonta Sahib",
        "Sundernagar",
        "Chamba",
    ],
    "Jharkhand": [
        "Ranchi",
        "Jamshedpur",
        "Dhanbad",
        "Bokaro",
        "Deoghar",
        "Phusro",
        "Hazaribagh",
        "Giridih",
        "Ramgarh",
        "Medininagar",
    ],
    "Karnataka": [
        "Bangalore",
        "Mysore",
        "Hubli",
        "Mangalore",
        "Belgaum",
        "Gulbarga",
        "Davanagere",
        "Bellary",
        "Bijapur",
        "Shimoga",
    ],
    "Kerala": [
        "Thiruvananthapuram",
        "Kochi",
        "Kozhikode",
        "Thrissur",
        "Kollam",
        "Palakkad",
        "Alappuzha",
        "Malappuram",
        "Kannur",
        "Kasaragod",
    ],
    "Madhya Pradesh": [
        "Bhopal",
        "Indore",
        "Gwalior",
        "Jabalpur",
        "Ujjain",
        "Sagar",
        "Dewas",
        "Satna",
        "Ratlam",
        "Rewa",
    ],
    "Maharashtra": [
        "Mumbai",
        "Pune",
        "Nagpur",
        "Thane",
        "Nashik",
        "Aurangabad",
        "Solapur",
        "Amravati",
        "Kolhapur",
        "Sangli",
    ],
    "Manipur": [
        "Imphal",
        "Thoubal",
        "Bishnupur",
        "Churachandpur",
        "Kakching",
        "Ukhrul",
        "Senapati",
        "Tamenglong",
        "Jiribam",
        "Moreh",
    ],
    "Meghalaya": [
        "Shillong",
        "Tura",
        "Cherrapunji",
        "Jowai",
        "Baghmara",
        "Nongpoh",
        "Mawkyrwat",
        "Resubelpara",
        "Ampati",
        "Williamnagar",
    ],
    "Mizoram": [
        "Aizawl",
        "Lunglei",
        "Saiha",
        "Champhai",
        "Kolasib",
        "Serchhip",
        "Mamit",
        "Lawngtlai",
        "Saitual",
        "Khawzawl",
    ],
    "Nagaland": [
        "Kohima",
        "Dimapur",
        "Mokokchung",
        "Tuensang",
        "Wokha",
        "Zunheboto",
        "Phek",
        "Kiphire",
        "Longleng",
        "Peren",
    ],
    "Odisha": [
        "Bhubaneswar",
        "Cuttack",
        "Rourkela",
        "Berhampur",
        "Sambalpur",
        "Puri",
        "Balasore",
        "Bhadrak",
        "Baripada",
        "Jharsuguda",
    ],
    "Punjab": [
        "Ludhiana",
        "Amritsar",
        "Jalandhar",
        "Patiala",
        "Bathinda",
        "Mohali",
        "Firozpur",
        "Batala",
        "Pathankot",
        "Moga",
    ],
    "Rajasthan": [
        "Jaipur",
        "Jodhpur",
        "Kota",
        "Bikaner",
        "Ajmer",
        "Udaipur",
        "Bhilwara",
        "Alwar",
        "Bharatpur",
        "Sikar",
    ],
    "Sikkim": [
        "Gangtok",
        "Namchi",
        "Geyzing",
        "Mangan",
        "Jorethang",
        "Nayabazar",
        "Rangpo",
        "Singtam",
        "Pakyong",
        "Ravangla",
    ],
    "Tamil Nadu": [
        "Chennai",
        "Coimbatore",
        "Madurai",
        "Tiruchirappalli",
        "Salem",
        "Tirunelveli",
        "Tiruppur",
        "Vellore",
        "Erode",
        "Thoothukkudi",
    ],
    "Telangana": [
        "Hyderabad",
        "Warangal",
        "Nizamabad",
        "Khammam",
        "Karimnagar",
        "Ramagundam",
        "Mahbubnagar",
        "Nalgonda",
        "Adilabad",
        "Suryapet",
    ],
    "Tripura": [
        "Agartala",
        "Dharmanagar",
        "Udaipur",
        "Kailasahar",
        "Belonia",
        "Khowai",
        "Ambassa",
        "Ranir Bazar",
        "Sonamura",
        "Kumarghat",
    ],
    "Uttar Pradesh": [
        "Lucknow",
        "Kanpur",
        "Ghaziabad",
        "Agra",
        "Varanasi",
        "Meerut",
        "Allahabad",
        "Bareilly",
        "Aligarh",
        "Moradabad",
    ],
    "Uttarakhand": [
        "Dehradun",
        "Haridwar",
        "Roorkee",
        "Haldwani",
        "Rudrapur",
        "Kashipur",
        "Rishikesh",
        "Kotdwar",
        "Pithoragarh",
        "Almora",
    ],
    "West Bengal": [
        "Kolkata",
        "Howrah",
        "Durgapur",
        "Asansol",
        "Siliguri",
        "Bardhaman",
        "Malda",
        "Baharampur",
        "Habra",
        "Kharagpur",
    ],
    "Andaman and Nicobar Islands": [
        "Port Blair",
        "Bamboo Flat",
        "Garacharma",
        "Diglipur",
        "Mayabunder",
        "Rangat",
        "Campbell Bay",
        "Car Nicobar",
        "Hut Bay",
        "Neil Island",
    ],
    "Chandigarh": ["Chandigarh"],
    "Dadra and Nagar Haveli and Daman and Diu": [
        "Daman",
        "Diu",
        "Silvassa",
        "Dadra",
        "Nagar Haveli",
    ],
    "Delhi": [
        "New Delhi",
        "North Delhi",
        "South Delhi",
        "East Delhi",
        "West Delhi",
        "Central Delhi",
        "North East Delhi",
        "North West Delhi",
        "South East Delhi",
        "South West Delhi",
    ],
    "Jammu and Kashmir": [
        "Srinagar",
        "Jammu",
        "Baramulla",
        "Anantnag",
        "Kupwara",
        "Pulwama",
        "Rajouri",
        "Kathua",
        "Udhampur",
        "Reasi",
    ],
    "Ladakh": [
        "Leh",
        "Kargil",
        "Nubra",
        "Zanskar",
        "Changthang",
        "Sham",
        "Rupshu",
        "Dras",
        "Sankoo",
        "Turtuk",
    ],
    "Lakshadweep": [
        "Kavaratti",
        "Agatti",
        "Minicoy",
        "Amini",
        "Andrott",
        "Kalpeni",
        "Kadmat",
        "Kiltan",
        "Chetlat",
        "Bitra",
    ],
    "Puducherry": [
        "Puducherry",
        "Karaikal",
        "Mahe",
        "Yanam",
        "Oulgaret",
        "Villianur",
        "Ariyankuppam",
        "Mannadipet",
        "Bahour",
        "Nettapakkam",
    ],
}


def get_indian_states():
    """Get list of Indian states"""
    return list(INDIAN_STATES_CITIES.keys())


def get_cities_by_state(state):
    """Get cities for a specific state"""
    return INDIAN_STATES_CITIES.get(state, [])


# ----------------------------
# Email Setup
# ----------------------------
SMTP_EMAIL = "snehashisdas842@gmail.com"
SMTP_PASSWORD = "qoch jgmy cmmd xths"
ADMIN_EMAILS = ["dassnehashis842@gmail.com"]


# ----------------------------
# Validation Helpers
# ----------------------------
def validate_user_data(data):
    """Manual validation for user data."""
    required_fields = [
        "First_Name",
        "Last_Name",
        "EmailID",
        "DOB",
        "PhoneNo",
        "Gender",
        "Address",
        "Role",
    ]  # UserId is auto-generated, so not required in input
    for field in required_fields:
        if field not in data or not data[field]:
            raise ValueError(f"Missing or empty field: {field}")

    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_pattern, data["EmailID"]):
        raise ValueError(
            "Invalid email format. Please enter a valid email address (e.g., user@example.com)"
        )

    if not isinstance(data["PhoneNo"], list) or not data["PhoneNo"]:
        raise ValueError("At least one phone number is required")
    for phone in data["PhoneNo"]:
        if not re.match(r"^\d{10}$", phone):
            raise ValueError(
                f"Invalid phone number format: {phone}. Phone number must be exactly 10 digits (e.g., 1234567890)"
            )

    try:
        datetime.strptime(data["DOB"], "%d-%m-%Y")
    except ValueError:
        raise ValueError(
            "Invalid date format. Please use dd-mm-yyyy format (e.g., 01-01-1990)"
        )

    valid_roles = ["Super_Admin", "Admin", "Employee", "Customer"]
    if data["Role"] not in valid_roles:
        raise ValueError(f'Invalid role. Must be one of: {", ".join(valid_roles)}')


def validate_login_data(data):
    """Manual validation for login data."""
    if not all(k in data for k in ["UserId", "Password"]):
        raise ValueError("Missing UserId or Password")


def validate_transaction_data(data):
    """Manual validation for transaction data."""
    if not all(k in data for k in ["amount", "type"]):
        raise ValueError("Missing amount or type")
    if not isinstance(data["amount"], (int, float)):
        raise ValueError("Amount must be a number")
    if data["type"] not in ["Credit", "Debit"]:
        raise ValueError("Invalid transaction type. Must be 'Credit' or 'Debit'.")


# ----------------------------
# Authentication Decorators
# ----------------------------
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
# ----------------------------
def get_all_roles():
    """Get all available roles"""
    try:
        return list(role_collection.find({}, {"_id": 0}))
    except Exception as e:
        print(f"Error getting roles: {e}")
        return []


def get_all_statuses():
    """Get all available statuses"""
    try:
        return list(status_collection.find({}, {"_id": 0}))
    except Exception as e:
        print(f"Error getting statuses: {e}")
        return []


def get_role_name(role_id):
    """Get role name by role_id"""
    try:
        role = role_collection.find_one({"role_id": role_id})
        return role["role_name"] if role else "Unknown"
    except Exception as e:
        print(f"Error getting role name: {e}")
        return "Unknown"


def get_status_name(status_id):
    """Get status name by status_id"""
    try:
        status = status_collection.find_one({"status_id": status_id})
        return status["status_name"] if status else "Unknown"
    except Exception as e:
        print(f"Error getting status name: {e}")
        return "Unknown"


# ----------------------------
# Helpers
# ----------------------------
def generate_password(dob: str) -> str:
    try:
        date_obj = datetime.strptime(dob, "%d-%m-%Y")
        formatted = date_obj.strftime("%d%m%Y")
        raw_password = f"Test@{formatted}"
        encoded_password = base64.b64encode(raw_password.encode("utf-8")).decode(
            "utf-8"
        )
        return encoded_password
    except Exception:
        raise ValueError("DOB must be in dd-mm-yyyy format")


def encode_password(pw: str) -> str:
    return base64.b64encode(pw.encode()).decode()


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
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(SMTP_EMAIL, SMTP_PASSWORD)
            smtp.send_message(msg)
    except Exception as e:
        print("Admin email failed:", e)


def generate_transaction_chart(user_id):
    """Generate a transaction chart for the user"""
    try:
        # Get user's transactions from last 6 months
        six_months_ago = datetime.now(timezone.utc) - timedelta(days=180)
        transactions = list(
            transactions_collection.find(
                {"UserId": user_id, "TransactionDate": {"$gte": six_months_ago}}
            ).sort("TransactionDate", 1)
        )

        if not transactions:
            return None

        # Prepare data for chart
        dates = []
        credits = []
        debits = []
        balance_over_time = []

        # Get current balance
        account = accounts_collection.find_one({"UserId": user_id})
        current_balance = account["Balance"] if account else 0

        # Group transactions by date
        daily_transactions = defaultdict(lambda: {"credit": 0, "debit": 0})

        for txn in transactions:
            txn_date = txn["TransactionDate"]
            if isinstance(txn_date, str):
                txn_date = datetime.fromisoformat(txn_date.replace("Z", "+00:00"))

            date_key = txn_date.strftime("%Y-%m-%d")
            amount = txn["TransactionAmount"]

            if txn["TransactionType"].lower() == "credit":
                daily_transactions[date_key]["credit"] += amount
            else:
                daily_transactions[date_key]["debit"] += amount

        # Create chart data
        running_balance = current_balance
        sorted_dates = sorted(daily_transactions.keys(), reverse=True)

        # Calculate balance over time (working backwards)
        for date_str in sorted_dates:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            dates.insert(0, date_obj)
            credits.insert(0, daily_transactions[date_str]["credit"])
            debits.insert(0, daily_transactions[date_str]["debit"])
            balance_over_time.insert(0, running_balance)

            # Adjust running balance for previous day
            running_balance = (
                running_balance
                - daily_transactions[date_str]["credit"]
                + daily_transactions[date_str]["debit"]
            )

        # Create the chart
        plt.style.use("default")
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        fig.suptitle(
            f"Transaction Summary - Last 6 Months", fontsize=16, fontweight="bold"
        )

        # Chart 1: Credit vs Debit
        width = 0.35
        x_pos = range(len(dates))

        bars1 = ax1.bar(
            [x - width / 2 for x in x_pos],
            credits,
            width,
            label="Credits",
            color="#27ae60",
            alpha=0.8,
        )
        bars2 = ax1.bar(
            [x + width / 2 for x in x_pos],
            debits,
            width,
            label="Debits",
            color="#e74c3c",
            alpha=0.8,
        )

        ax1.set_xlabel("Date")
        ax1.set_ylabel("Amount (₹)")
        ax1.set_title("Daily Credits vs Debits")
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Format x-axis dates
        if len(dates) > 10:
            step = len(dates) // 10
            ax1.set_xticks([x for x in x_pos[::step]])
            ax1.set_xticklabels(
                [dates[i].strftime("%m/%d") for i in range(0, len(dates), step)],
                rotation=45,
            )
        else:
            ax1.set_xticks(x_pos)
            ax1.set_xticklabels([d.strftime("%m/%d") for d in dates], rotation=45)

        # Chart 2: Balance over time
        ax2.plot(
            dates,
            balance_over_time,
            marker="o",
            linewidth=2,
            markersize=4,
            color="#3498db",
        )
        ax2.fill_between(dates, balance_over_time, alpha=0.3, color="#3498db")
        ax2.set_xlabel("Date")
        ax2.set_ylabel("Balance (₹)")
        ax2.set_title("Account Balance Over Time")
        ax2.grid(True, alpha=0.3)

        # Format dates on x-axis
        ax2.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
        ax2.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)

        # Add summary statistics
        total_credits = sum(credits)
        total_debits = sum(debits)
        net_change = total_credits - total_debits

        summary_text = f"""
Summary Statistics:
• Total Credits: ₹{total_credits:,.2f}
• Total Debits: ₹{total_debits:,.2f}
• Net Change: ₹{net_change:,.2f}
• Current Balance: ₹{current_balance:,.2f}
• Transactions: {len(transactions)}
        """

        fig.text(
            0.02,
            0.02,
            summary_text,
            fontsize=10,
            verticalalignment="bottom",
            bbox=dict(boxstyle="round", facecolor="lightgray", alpha=0.8),
        )

        plt.tight_layout()
        plt.subplots_adjust(bottom=0.15)

        # Save chart to bytes
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format="png", dpi=300, bbox_inches="tight")
        img_buffer.seek(0)
        plt.close()

        return img_buffer.getvalue()

    except Exception as e:
        print(f"Error generating transaction chart: {e}")
        return None


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

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(SMTP_EMAIL, SMTP_PASSWORD)
            smtp.send_message(msg)

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

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(SMTP_EMAIL, SMTP_PASSWORD)
            smtp.send_message(msg)
        print(f"Monthly report sent to admin emails: {', '.join(ADMIN_EMAILS)}")
    except Exception as e:
        print(f"Failed to send monthly report: {e}")


def create_accounts_for_customers():
    """
    Creates bank accounts for all users with the 'Customer' role.
    This function is run on application startup.
    """
    try:
        for user in users_collection.find({"Role": "Customer"}):
            if not accounts_collection.find_one({"UserId": user["UserId"]}):
                branch = (
                    user.get("Address", "Unknown").strip().split()[0]
                    if user.get("Address")
                    else "Unknown"
                )
                account_doc = {
                    "UserId": user["UserId"],
                    "Balance": 0,
                    "Branch": branch,
                    "ActivityStatus": "Active",
                    "LastTransaction": datetime.now(),
                }
                accounts_collection.insert_one(account_doc)
        print("Accounts created for new Customers.")
    except Exception as e:
        print(f"Error creating customer accounts: {e}")


def create_transaction(user_id, account_id, amount, txn_type):
    """
    Records a new transaction in the transactions collection.
    """
    try:
        transaction_doc = {
            "TransactionId": "TXN" + str(uuid.uuid4().hex[:8].upper()),
            "UserId": user_id,
            "AccountId": account_id,
            "TransactionAmount": amount,
            "TransactionDate": datetime.now(),
            "TransactionType": txn_type,
        }
        transactions_collection.insert_one(transaction_doc)
        print("Transaction created ✅")
        return transaction_doc
    except Exception as e:
        print(f"Failed to create transaction: {e}")
        return None
