"""MongoDB connection, collections, indexes, and reference-data setup."""
import time
import uuid
from datetime import datetime, timezone
from pymongo import MongoClient
from app.config import Config


# ----------------------------
# MongoDB Connection with Connection Pooling
# ----------------------------
client = MongoClient(
    Config.MONGO_URI,
    maxPoolSize=50,
    minPoolSize=10,
    maxIdleTimeMS=30000,
    waitQueueTimeoutMS=5000,
)
db = client[Config.DB_NAME]
users_collection = db["users"]
login_history_collection = db["login_history"]
accounts_collection = db["accounts"]
transactions_collection = db["transactions"]
role_collection = db["role"]
status_collection = db["status"]
counters_collection = db["counters"]  # For auto-incrementing User IDs


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


def setup_database():
    """Call once at app startup — creates indexes and seeds reference data."""
    create_indexes()
    initialize_reference_data()


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
        return str(int(time.time()))

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
                    "LastTransaction": datetime.now(timezone.utc),
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
            "TransactionDate": datetime.now(timezone.utc),
            "TransactionType": txn_type,
        }
        transactions_collection.insert_one(transaction_doc)
        print("Transaction created ✅")
        return transaction_doc
    except Exception as e:
        print(f"Failed to create transaction: {e}")
        return None
