"""
Manager actions — backend logic for the human-in-the-loop lifecycle.

When a manager approves or denies a refund, this module:
  1. Updates the refund record in the database
  2. Processes the refund if approved (calls process_refund tool)
  3. Sends a confirmation or denial email to the customer
  4. Closes the related support ticket

This is the "completion loop" — the piece that connects
the manager's decision back to the automated workflow.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime

from src.utils.database import get_connection
from src.tools.email import send_email
from src.tools.tickets import update_ticket, close_ticket
from src.tools.refunds import process_refund


def get_pending_refunds() -> list[dict]:
    """Get all refunds awaiting manager approval."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT r.id, r.order_id, r.customer_id, r.amount, r.reason, r.created_at, "
        "c.name as customer_name, c.email as customer_email, c.plan as customer_plan, "
        "o.product, o.total as order_total "
        "FROM refunds r "
        "JOIN customers c ON r.customer_id = c.id "
        "JOIN orders o ON r.order_id = o.id "
        "WHERE r.status = 'pending' "
        "ORDER BY r.created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_open_tickets() -> list[dict]:
    """Get all open support tickets."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT t.id, t.customer_id, t.subject, t.status, t.priority, "
        "t.category, t.created_at, t.updated_at, "
        "c.name as customer_name, c.email as customer_email "
        "FROM tickets t "
        "JOIN customers c ON t.customer_id = c.id "
        "WHERE t.status = 'open' "
        "ORDER BY "
        "CASE t.priority "
        "  WHEN 'urgent' THEN 1 "
        "  WHEN 'high' THEN 2 "
        "  WHEN 'medium' THEN 3 "
        "  WHEN 'low' THEN 4 "
        "END, t.created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_recent_refunds(limit: int = 20) -> list[dict]:
    """Get recently processed refunds."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT r.id, r.order_id, r.customer_id, r.amount, r.reason, "
        "r.status, r.approved_by, r.created_at, "
        "c.name as customer_name, o.product "
        "FROM refunds r "
        "JOIN customers c ON r.customer_id = c.id "
        "JOIN orders o ON r.order_id = o.id "
        "ORDER BY r.created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_dashboard_stats() -> dict:
    """Get summary statistics for the dashboard header."""
    conn = get_connection()

    pending_refunds = conn.execute(
        "SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as total FROM refunds WHERE status = 'pending'"
    ).fetchone()

    open_tickets = conn.execute(
        "SELECT COUNT(*) as count FROM tickets WHERE status = 'open'"
    ).fetchone()

    completed_refunds = conn.execute(
        "SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as total FROM refunds WHERE status = 'completed'"
    ).fetchone()

    resolved_tickets = conn.execute(
        "SELECT COUNT(*) as count FROM tickets WHERE status = 'resolved'"
    ).fetchone()

    conn.close()

    return {
        "pending_refunds_count": pending_refunds["count"],
        "pending_refunds_total": pending_refunds["total"],
        "open_tickets_count": open_tickets["count"],
        "completed_refunds_count": completed_refunds["count"],
        "completed_refunds_total": completed_refunds["total"],
        "resolved_tickets_count": resolved_tickets["count"],
    }


def approve_refund(refund_id: str, manager_name: str = "Manager") -> str:
    """
    Approve a pending refund — the full lifecycle:
      1. Update refund status to 'completed'
      2. Process the actual refund
      3. Email the customer
      4. Find and close the related ticket
    """
    conn = get_connection()

    # Get refund details
    refund = conn.execute(
        "SELECT r.*, c.name as customer_name, c.email as customer_email, o.product "
        "FROM refunds r "
        "JOIN customers c ON r.customer_id = c.id "
        "JOIN orders o ON r.order_id = o.id "
        "WHERE r.id = ?",
        (refund_id,),
    ).fetchone()

    if not refund:
        conn.close()
        return f"Refund {refund_id} not found"

    if refund["status"] != "pending":
        conn.close()
        return f"Refund {refund_id} is already {refund['status']}"

    # 1. Update refund record
    now = datetime.utcnow().isoformat()
    conn.execute(
        "UPDATE refunds SET status = 'completed', approved_by = ? WHERE id = ?",
        (manager_name, refund_id),
    )
    conn.commit()
    conn.close()

    # 2. Send confirmation email to customer
    send_email.invoke({
        "to": refund["customer_email"],
        "subject": f"Refund Approved — ${refund['amount']:.2f} for {refund['product']}",
        "body": (
            f"Hi {refund['customer_name']},\n\n"
            f"Your refund of ${refund['amount']:.2f} for {refund['product']} "
            f"(Order: {refund['order_id']}) has been approved and processed.\n\n"
            f"The refund will appear on your original payment method within 3-5 business days.\n\n"
            f"Thank you for your patience.\n"
            f"— TechGear Support"
        ),
    })

    # 3. Find and close related ticket
    conn = get_connection()
    ticket = conn.execute(
        "SELECT id FROM tickets WHERE customer_id = ? AND status = 'open' ORDER BY created_at DESC LIMIT 1",
        (refund["customer_id"],),
    ).fetchone()
    conn.close()

    if ticket:
        update_ticket.invoke({
            "ticket_id": ticket["id"],
            "message": f"Refund {refund_id} approved by {manager_name}. Amount: ${refund['amount']:.2f}",
        })
        close_ticket.invoke({
            "ticket_id": ticket["id"],
            "resolution": f"Refund of ${refund['amount']:.2f} approved and processed",
        })

    return f"Refund {refund_id} approved. ${refund['amount']:.2f} refunded to {refund['customer_name']}. Email sent."


def deny_refund(refund_id: str, reason: str, manager_name: str = "Manager") -> str:
    """
    Deny a pending refund:
      1. Update refund status to 'rejected'
      2. Email the customer with the reason
      3. Update the related ticket
    """
    conn = get_connection()

    refund = conn.execute(
        "SELECT r.*, c.name as customer_name, c.email as customer_email, o.product "
        "FROM refunds r "
        "JOIN customers c ON r.customer_id = c.id "
        "JOIN orders o ON r.order_id = o.id "
        "WHERE r.id = ?",
        (refund_id,),
    ).fetchone()

    if not refund:
        conn.close()
        return f"Refund {refund_id} not found"

    if refund["status"] != "pending":
        conn.close()
        return f"Refund {refund_id} is already {refund['status']}"

    # 1. Update refund record
    conn.execute(
        "UPDATE refunds SET status = 'rejected', approved_by = ? WHERE id = ?",
        (manager_name, refund_id),
    )
    conn.commit()
    conn.close()

    # 2. Email the customer
    send_email.invoke({
        "to": refund["customer_email"],
        "subject": f"Refund Update — {refund['product']}",
        "body": (
            f"Hi {refund['customer_name']},\n\n"
            f"After review, we were unable to approve the refund of ${refund['amount']:.2f} "
            f"for {refund['product']} (Order: {refund['order_id']}).\n\n"
            f"Reason: {reason}\n\n"
            f"If you have questions about this decision, please reply to this email "
            f"or contact our support team.\n\n"
            f"— TechGear Support"
        ),
    })

    # 3. Update related ticket
    conn = get_connection()
    ticket = conn.execute(
        "SELECT id FROM tickets WHERE customer_id = ? AND status = 'open' ORDER BY created_at DESC LIMIT 1",
        (refund["customer_id"],),
    ).fetchone()
    conn.close()

    if ticket:
        update_ticket.invoke({
            "ticket_id": ticket["id"],
            "message": f"Refund {refund_id} denied by {manager_name}. Reason: {reason}",
        })

    return f"Refund {refund_id} denied. Customer {refund['customer_name']} notified via email."
