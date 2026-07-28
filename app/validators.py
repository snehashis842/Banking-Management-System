"""Manual request-payload validators shared by the route handlers."""
import re
from datetime import datetime


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


def validate_signup_data(data):
    """Manual validation for public self-signup data (Customer role only).
    Password is not collected here — every new account starts with the
    default Test@DDMMYYYY password derived from DOB, same as admin-created
    accounts. Users change it later via a separate change-password flow."""
    required_fields = [
        "First_Name",
        "Last_Name",
        "EmailID",
        "DOB",
        "PhoneNo",
        "Gender",
        "Address",
    ]
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
