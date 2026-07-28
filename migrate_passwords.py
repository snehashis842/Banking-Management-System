"""
migrate_passwords.py — one-time bulk fix for accounts created before the
password-hashing update. Resets any non-hashed password to the DOB-derived
default (Test@DDMMYYYY), hashed correctly.

Usage:
    python migrate_passwords.py
"""
from app.db import users_collection
from app.security import hash_password, generate_password


def looks_like_werkzeug_hash(value: str) -> bool:
    return isinstance(value, str) and ":" in value and value.split(":")[0] in (
        "scrypt",
        "pbkdf2",
    )


def main():
    users = list(users_collection.find({}))
    if not users:
        print("No users found.")
        return

    fixed = []
    skipped = []

    for user in users:
        user_id = user.get("UserId")
        dob = user.get("DOB")
        old_password = user.get("Password", "")

        if looks_like_werkzeug_hash(old_password):
            skipped.append(user_id)
            continue

        if not dob:
            print(f"Skipping {user_id}: no DOB on record, cannot derive default password.")
            continue

        try:
            raw_password = generate_password(dob)
        except ValueError as e:
            print(f"Skipping {user_id}: {e}")
            continue

        hashed = hash_password(raw_password)
        users_collection.update_one({"UserId": user_id}, {"$set": {"Password": hashed}})
        fixed.append((user_id, raw_password))

    print(f"\nMigrated {len(fixed)} user(s):")
    for user_id, raw_password in fixed:
        print(f"  {user_id}  ->  {raw_password}")

    print(f"\nAlready OK (skipped): {len(skipped)} user(s)")
    if skipped:
        print(f"  {', '.join(skipped)}")


if __name__ == "__main__":
    main()
