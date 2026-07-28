"""Matplotlib transaction chart generation."""
import io
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import matplotlib
matplotlib.use("Agg")  # non-interactive backend, required for server-side rendering
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from app.db import accounts_collection, transactions_collection


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

