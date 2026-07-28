"""Role and status ID <-> name lookups against the reference collections."""
from app.db import role_collection, status_collection


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
