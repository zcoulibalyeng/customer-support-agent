"""
Order tools — look up orders, check status, get tracking info.
"""

from langchain_core.tools import tool

from src.utils.database import get_connection


@tool
def get_order_status(order_id: str) -> str:
    """Check the current status of an order by order ID. Returns order details including product, status, and tracking."""
    conn = get_connection()
    row = conn.execute(
        "SELECT id, customer_id, product, quantity, total, status, tracking_number, ordered_at, delivered_at FROM orders WHERE id = ?",
        (order_id,),
    ).fetchone()
    conn.close()

    if not row:
        return f"No order found with ID: {order_id}"

    result = (
        f"Order ID: {row['id']}\n"
        f"Product: {row['product']}\n"
        f"Quantity: {row['quantity']}\n"
        f"Total: ${row['total']:.2f}\n"
        f"Status: {row['status']}\n"
        f"Ordered: {row['ordered_at']}"
    )

    if row["tracking_number"]:
        result += f"\nTracking: {row['tracking_number']}"
    if row["delivered_at"]:
        result += f"\nDelivered: {row['delivered_at']}"

    return result


@tool
def get_customer_orders(customer_id: str) -> str:
    """Get all orders for a customer. Returns a list of their order history."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, product, total, status, ordered_at FROM orders WHERE customer_id = ? ORDER BY ordered_at DESC",
        (customer_id,),
    ).fetchall()
    conn.close()

    if not rows:
        return f"No orders found for customer {customer_id}"

    lines = [f"Orders for customer {customer_id}:\n"]
    for row in rows:
        lines.append(f"  {row['id']} | {row['product']} | ${row['total']:.2f} | {row['status']} | {row['ordered_at']}")
    return "\n".join(lines)


@tool
def get_order_for_refund(order_id: str) -> str:
    """Get order details needed to process a refund. Returns order info with refund eligibility."""
    conn = get_connection()
    row = conn.execute(
        "SELECT o.id, o.customer_id, o.product, o.total, o.status, o.ordered_at, c.plan "
        "FROM orders o JOIN customers c ON o.customer_id = c.id WHERE o.id = ?",
        (order_id,),
    ).fetchone()
    conn.close()

    if not row:
        return f"No order found with ID: {order_id}"

    eligible = row["status"] in ("delivered", "shipped")

    return (
        f"Order ID: {row['id']}\n"
        f"Customer ID: {row['customer_id']}\n"
        f"Product: {row['product']}\n"
        f"Total: ${row['total']:.2f}\n"
        f"Status: {row['status']}\n"
        f"Customer plan: {row['plan']}\n"
        f"Refund eligible: {'Yes' if eligible else 'No — order status is ' + row['status']}"
    )
