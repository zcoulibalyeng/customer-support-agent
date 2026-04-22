"""
Manager Dashboard — human-in-the-loop approval interface.

Shows pending refund approvals, open tickets, and recent activity.
When a manager approves/denies a refund, the system automatically:
  - Processes or rejects the refund
  - Emails the customer
  - Updates and closes the ticket

Usage:
    streamlit run ui/manager.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from src.utils.database import init_database
from src.workflow.manager_actions import (
    approve_refund,
    deny_refund,
    get_dashboard_stats,
    get_open_tickets,
    get_pending_refunds,
    get_recent_refunds,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Manager Dashboard — TechGear",
    page_icon="📊",
    layout="wide",
)

if "initialised" not in st.session_state:
    init_database()
    st.session_state.initialised = True


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.title("📊 Manager Dashboard")
st.caption("Human-in-the-loop oversight for the TechGear Support Agent")

# Refresh button
if st.button("🔄 Refresh", type="secondary"):
    st.rerun()

st.divider()


# ---------------------------------------------------------------------------
# Stats row
# ---------------------------------------------------------------------------

stats = get_dashboard_stats()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Pending refunds", stats["pending_refunds_count"], f"${stats['pending_refunds_total']:.2f}")

with col2:
    st.metric("Open tickets", stats["open_tickets_count"])

with col3:
    st.metric("Refunds processed", stats["completed_refunds_count"], f"${stats['completed_refunds_total']:.2f}")

with col4:
    st.metric("Tickets resolved", stats["resolved_tickets_count"])

st.divider()


# ---------------------------------------------------------------------------
# Pending refund approvals
# ---------------------------------------------------------------------------

st.header("⏳ Pending refund approvals")

pending = get_pending_refunds()

if not pending:
    st.info("No pending refunds. All caught up!")
else:
    for refund in pending:
        with st.container(border=True):
            left, right = st.columns([3, 1])

            with left:
                st.subheader(f"${refund['amount']:.2f} — {refund['product']}")
                st.markdown(
                    f"**Customer:** {refund['customer_name']} ({refund['customer_email']}) · "
                    f"**Plan:** {refund['customer_plan']}  \n"
                    f"**Order:** {refund['order_id']} · **Order total:** ${refund['order_total']:.2f}  \n"
                    f"**Reason:** {refund['reason']}  \n"
                    f"**Requested:** {refund['created_at']}"
                )

            with right:
                st.markdown("###")  # vertical spacer

                manager_name = st.text_input(
                    "Your name",
                    value="Manager",
                    key=f"name_{refund['id']}",
                    label_visibility="collapsed",
                    placeholder="Your name",
                )

                approve_col, deny_col = st.columns(2)

                with approve_col:
                    if st.button("✅ Approve", key=f"approve_{refund['id']}", type="primary", use_container_width=True):
                        result = approve_refund(refund["id"], manager_name)
                        st.success(result)
                        st.rerun()

                with deny_col:
                    if st.button("❌ Deny", key=f"deny_{refund['id']}", use_container_width=True):
                        st.session_state[f"show_deny_{refund['id']}"] = True

                # Denial reason form
                if st.session_state.get(f"show_deny_{refund['id']}", False):
                    reason = st.text_input(
                        "Denial reason",
                        key=f"reason_{refund['id']}",
                        placeholder="e.g., Outside return window",
                    )
                    if reason and st.button("Confirm denial", key=f"confirm_deny_{refund['id']}"):
                        result = deny_refund(refund["id"], reason, manager_name)
                        st.warning(result)
                        del st.session_state[f"show_deny_{refund['id']}"]
                        st.rerun()

st.divider()


# ---------------------------------------------------------------------------
# Open tickets
# ---------------------------------------------------------------------------

st.header("🎫 Open tickets")

tickets = get_open_tickets()

if not tickets:
    st.info("No open tickets.")
else:
    for ticket in tickets:
        priority_colors = {"urgent": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
        icon = priority_colors.get(ticket["priority"], "⚪")

        with st.expander(f"{icon} {ticket['id']} — {ticket['subject']} ({ticket['customer_name']})"):
            st.markdown(
                f"**Customer:** {ticket['customer_name']} ({ticket['customer_email']})  \n"
                f"**Priority:** {ticket['priority']} · **Category:** {ticket['category'] or 'uncategorised'}  \n"
                f"**Created:** {ticket['created_at']}  \n"
                f"**Last updated:** {ticket['updated_at']}"
            )

st.divider()


# ---------------------------------------------------------------------------
# Recent refund activity
# ---------------------------------------------------------------------------

st.header("📋 Recent refund activity")

recent = get_recent_refunds()

if not recent:
    st.info("No refund activity yet.")
else:
    # Build a simple table
    table_data = []
    for r in recent:
        status_icon = {"completed": "✅", "rejected": "❌", "pending": "⏳"}.get(r["status"], "❓")
        table_data.append(
            {
                "ID": r["id"],
                "Customer": r["customer_name"],
                "Product": r["product"],
                "Amount": f"${r['amount']:.2f}",
                "Status": f"{status_icon} {r['status']}",
                "Approved by": r["approved_by"] or "—",
                "Date": r["created_at"][:16],
            }
        )

    st.dataframe(table_data, width="stretch", hide_index=True)
