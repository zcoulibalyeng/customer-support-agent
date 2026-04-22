"""
Customer tools — look up and update customer accounts.

Each function is a LangChain @tool that the agent can invoke
through native function calling.
"""

from langchain_core.tools import tool
from src.utils.database import get_connection


@tool
def lookup_customer(email: str) -> str:
    """Look up a customer by their email address. Returns customer details including ID, name, plan, and account notes."""
    conn = get_connection()
    row = conn.execute(
        "SELECT id, name, email, plan, created_at, notes FROM customers WHERE email = ?",
        (email,),
    ).fetchone()
    conn.close()

    if not row:
        return f"No customer found with email: {email}"

    return (
        f"Customer ID: {row['id']}\n"
        f"Name: {row['name']}\n"
        f"Email: {row['email']}\n"
        f"Plan: {row['plan']}\n"
        f"Member since: {row['created_at']}\n"
        f"Notes: {row['notes'] or 'None'}"
    )


@tool
def lookup_customer_by_id(customer_id: str) -> str:
    """Look up a customer by their customer ID. Returns full customer profile."""
    conn = get_connection()
    row = conn.execute(
        "SELECT id, name, email, plan, created_at, notes FROM customers WHERE id = ?",
        (customer_id,),
    ).fetchone()
    conn.close()

    if not row:
        return f"No customer found with ID: {customer_id}"

    return (
        f"Customer ID: {row['id']}\n"
        f"Name: {row['name']}\n"
        f"Email: {row['email']}\n"
        f"Plan: {row['plan']}\n"
        f"Member since: {row['created_at']}\n"
        f"Notes: {row['notes'] or 'None'}"
    )
