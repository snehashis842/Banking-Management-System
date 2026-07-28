"""Password hashing and generation. No plaintext or base64 "hashing" here."""
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


def generate_password(dob: str) -> str:
    """Generate a temporary raw password for admin-created users, based on DOB.
    Returned value is PLAINTEXT — caller must hash it with hash_password()
    before storing, and show this raw value to the admin exactly once so it
    can be shared with the user (who should reset it after first login)."""
    try:
        date_obj = datetime.strptime(dob, "%d-%m-%Y")
        return f"Test@{date_obj.strftime('%d%m%Y')}"
    except Exception:
        raise ValueError("DOB must be in dd-mm-yyyy format")


def hash_password(raw_password: str) -> str:
    """Hash a plaintext password for storage. Never store raw passwords."""
    return generate_password_hash(raw_password)


def verify_password(raw_password: str, hashed_password: str) -> bool:
    """Check a plaintext password attempt against a stored hash."""
    try:
        return check_password_hash(hashed_password, raw_password)
    except Exception:
        return False

