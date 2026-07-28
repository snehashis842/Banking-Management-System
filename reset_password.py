"""
reset_password.py — one-off utility to fix accounts created before the
password-hashing update (e.g. anything inserted manually via mongosh).

Usage:
    python reset_password.py <UserId> <NewPassword>

Example:
    python reset_password.py 56125810021 Test@15052001
"""
import sys
from app.db import users_collection
from app.security import hash_password


def main():
    if len(sys.argv) != 3:
        print("Usage: python reset_password.py <UserId> <NewPassword>")
        sys.exit(1)

    user_id = sys.argv[1]
    new_password = sys.argv[2]

    if len(new_password) < 8:
        print("Password must be at least 8 characters long.")
        sys.exit(1)

    user = users_collection.find_one({"UserId": user_id})
    if not user:
        print(f"No user found with UserId: {user_id}")
        sys.exit(1)

    hashed = hash_password(new_password)
    result = users_collection.update_one(
        {"UserId": user_id}, {"$set": {"Password": hashed}}
    )

    if result.modified_count == 1:
        print(f"Password updated for {user_id}. New login password: {new_password}")
    else:
        print("Update failed — no document modified.")


if __name__ == "__main__":
    main()
