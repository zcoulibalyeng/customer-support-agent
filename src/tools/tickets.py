"""
Ticket tools — create, update, and close support tickets.
"""

import json
import uuid
from datetime import datetime

from langchain_core.tools import tool

from src.utils.database import get_connection


@tool
def create_ticket(customer_id: str, subject: str, category: str, priority: str = "medium") -> str:
    """Create a new support ticket for a customer. Returns the new ticket ID."""
    ticket_id = f"TKT-{uuid.uuid4().hex[:6].upper()}"
    now = datetime.utcnow().isoformat()

    conn = get_connection()
    conn.execute(
        "INSERT INTO tickets (id, customer_id, subject, status, priority, category, messages, created_at, updated_at) "
        "VALUES (?, ?, ?, 'open', ?, ?, '[]', ?, ?)",
        (ticket_id, customer_id, subject, priority, category, now, now),
    )
    conn.commit()
    conn.close()

    return f"Ticket created: {ticket_id} | Subject: {subject} | Priority: {priority}"


@tool
def update_ticket(ticket_id: str, message: str) -> str:
    """Add a message to an existing ticket and update its timestamp."""
    conn = get_connection()
    row = conn.execute("SELECT messages FROM tickets WHERE id = ?", (ticket_id,)).fetchone()

    if not row:
        conn.close()
        return f"No ticket found with ID: {ticket_id}"

    messages = json.loads(row["messages"])
    messages.append(
        {
            "timestamp": datetime.utcnow().isoformat(),
            "content": message,
            "from": "agent",
        }
    )

    conn.execute(
        "UPDATE tickets SET messages = ?, updated_at = ? WHERE id = ?",
        (json.dumps(messages), datetime.utcnow().isoformat(), ticket_id),
    )
    conn.commit()
    conn.close()

    return f"Ticket {ticket_id} updated with message"


@tool
def close_ticket(ticket_id: str, resolution: str) -> str:
    """Close a support ticket with a resolution note."""
    now = datetime.utcnow().isoformat()
    conn = get_connection()

    result = conn.execute(
        "UPDATE tickets SET status = 'resolved', resolved_at = ?, updated_at = ? WHERE id = ?",
        (now, now, ticket_id),
    )
    conn.commit()
    conn.close()

    if result.rowcount == 0:
        return f"No ticket found with ID: {ticket_id}"

    return f"Ticket {ticket_id} closed. Resolution: {resolution}"


@tool
def get_customer_tickets(customer_id: str) -> str:
    """Get all tickets for a customer. Returns open and resolved tickets."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, subject, status, priority, category, created_at FROM tickets "
        "WHERE customer_id = ? ORDER BY created_at DESC",
        (customer_id,),
    ).fetchall()
    conn.close()

    if not rows:
        return f"No tickets found for customer {customer_id}"

    lines = [f"Tickets for customer {customer_id}:\n"]
    for row in rows:
        lines.append(f"  {row['id']} | {row['subject']} | {row['status']} | {row['priority']} | {row['created_at']}")
    return "\n".join(lines)
