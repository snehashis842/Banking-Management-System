"""Making transactions, viewing transaction history, chart download."""
from datetime import datetime, timedelta, timezone
from flask import Blueprint, render_template, request, jsonify, Response

from app.db import accounts_collection, transactions_collection, create_transaction
from app.validators import validate_transaction_data
from app.auth import get_current_user, require_admin_or_employee
from app.charts import generate_transaction_chart
from app.extensions import cache

transaction_bp = Blueprint("transaction", __name__)


@transaction_bp.route("/transaction_page")
@get_current_user
def show_transaction_page(current_user):
    if current_user["Role"] != "Customer":
        return jsonify({"detail": "Only customers can access this page."}), 403

    account = accounts_collection.find_one({"UserId": current_user["UserId"]})
    balance = account["Balance"] if account else 0
    return render_template("make_transaction.html", user=current_user, balance=balance)


@transaction_bp.route("/make_transaction", methods=["POST"])
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


@transaction_bp.route("/view_transactions_page")
@require_admin_or_employee
def show_transactions_page(current_user):
    return render_template("view_transactions.html", user=current_user)


@transaction_bp.route("/get_transactions")
@require_admin_or_employee
@cache.cached(timeout=30)
def get_transactions(current_user):
    try:
        three_months_ago = datetime.now(timezone.utc) - timedelta(days=90)
        transactions = list(
            transactions_collection.find(
                {"TransactionDate": {"$gte": three_months_ago}},
                {"_id": 0},
            )
            .sort("TransactionDate", -1)
            .limit(1000)
        )

        for txn in transactions:
            if isinstance(txn["TransactionDate"], datetime):
                txn["TransactionDate"] = txn["TransactionDate"].isoformat()

        return jsonify({"transactions": transactions})
    except Exception as e:
        return jsonify({"detail": f"Failed to retrieve transactions: {str(e)}"}), 500


@transaction_bp.route("/download_transaction_chart")
@get_current_user
def download_transaction_chart(current_user):
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

        return Response(
            chart_data,
            mimetype="image/png",
            headers={
                "Content-Disposition": f'attachment; filename=transaction_chart_{current_user["UserId"]}.png'
            },
        )
    except Exception as e:
        return jsonify({"detail": f"Failed to generate chart: {str(e)}"}), 500
