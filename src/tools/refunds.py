"""
Refund tools — issue refunds with automatic guardrail checks.

Refunds below MAX_AUTO_REFUND are processed automatically.
Refunds above require human approval via LangGraph interrupt.
"""

import uuid
from datetime import datetime

from langchain_core.tools import tool

from src.utils.database import get_connection
from src.utils.config import MAX_AUTO_REFUND


@tool
def check_refund_eligibility(order_id: str) -> str:
    """Check if an order is eligible for a refund and what the maximum refund amount would be."""
    conn = get_connection()
    row = conn.execute(
        "SELECT o.id, o.total, o.status, o.product, c.plan FROM orders o "
        "JOIN customers c ON o.customer_id = c.id WHERE o.id = ?",
        (order_id,),
    ).fetchone()
    conn.close()

    if not row:
        return f"No order found: {order_id}"

    # Check existing refunds
    conn = get_connection()
    existing = conn.execute(
        "SELECT SUM(amount) as refunded FROM refunds WHERE order_id = ? AND status != 'rejected'",
        (order_id,),
    ).fetchone()
    conn.close()

    already_refunded = existing["refunded"] or 0
    max_refund = row["total"] - already_refunded

    if row["status"] not in ("delivered", "shipped"):
        return f"Order {order_id} is not eligible for refund (status: {row['status']})"

    auto_limit = MAX_AUTO_REFUND
    requires_approval = max_refund > auto_limit

    return (
        f"Order: {order_id}\n"
        f"Product: {row['product']}\n"
        f"Order total: ${row['total']:.2f}\n"
        f"Already refunded: ${already_refunded:.2f}\n"
        f"Maximum refund available: ${max_refund:.2f}\n"
        f"Auto-approval limit: ${auto_limit:.2f}\n"
        f"Requires human approval: {'Yes' if requires_approval else 'No'}"
    )


@tool
def process_refund(order_id: str, amount: float, reason: str) -> str:
    """Process a refund for an order ONLY if the amount is within the auto-approval limit ($50). For larger amounts, use request_refund_approval instead."""
    conn = get_connection()

    order = conn.execute("SELECT customer_id, total FROM orders WHERE id = ?", (order_id,)).fetchone()
    if not order:
        conn.close()
        return f"Cannot process refund: order {order_id} not found"

    if amount > MAX_AUTO_REFUND:
        conn.close()
        return (
            f"Cannot auto-process: ${amount:.2f} exceeds the ${MAX_AUTO_REFUND:.2f} auto-approval limit. "
            f"Use request_refund_approval to submit this for manager review."
        )

    refund_id = f"REF-{uuid.uuid4().hex[:6].upper()}"
    now = datetime.utcnow().isoformat()

    conn.execute(
        "INSERT INTO refunds (id, order_id, customer_id, amount, reason, status, approved_by, created_at) "
        "VALUES (?, ?, ?, ?, ?, 'completed', 'auto', ?)",
        (refund_id, order_id, order["customer_id"], amount, reason, now),
    )
    conn.commit()
    conn.close()

    return (
        f"Refund processed automatically!\n"
        f"Refund ID: {refund_id}\n"
        f"Amount: ${amount:.2f}\n"
        f"Order: {order_id}"
    )


@tool
def request_refund_approval(order_id: str, amount: float, reason: str) -> str:
    """Submit a refund for manager approval. Use this when the refund amount exceeds the auto-approval limit ($50). The manager will review and approve/deny via the dashboard."""
    conn = get_connection()

    order = conn.execute("SELECT customer_id, total FROM orders WHERE id = ?", (order_id,)).fetchone()
    if not order:
        conn.close()
        return f"Cannot request refund: order {order_id} not found"

    refund_id = f"REF-{uuid.uuid4().hex[:6].upper()}"
    now = datetime.utcnow().isoformat()

    conn.execute(
        "INSERT INTO refunds (id, order_id, customer_id, amount, reason, status, approved_by, created_at) "
        "VALUES (?, ?, ?, ?, ?, 'pending', NULL, ?)",
        (refund_id, order_id, order["customer_id"], amount, reason, now),
    )
    conn.commit()
    conn.close()

    return (
        f"Refund submitted for manager approval.\n"
        f"Refund ID: {refund_id}\n"
        f"Amount: ${amount:.2f}\n"
        f"Order: {order_id}\n"
        f"Status: Pending manager review\n"
        f"The customer will be notified once the manager approves or denies the request."
    )
