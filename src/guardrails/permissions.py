"""
Permission guardrails — action-level checks.

Wraps sensitive tool calls with policy enforcement.
Called by the agent before executing high-risk actions.
"""

from src.utils.config import MAX_AUTO_REFUND


def check_refund_permission(amount: float) -> dict:
    """
    Check if a refund amount can be auto-approved.

    Returns:
        dict with 'allowed' (bool) and 'reason' (str)
    """
    if amount <= 0:
        return {"allowed": False, "reason": "Refund amount must be positive"}

    if amount <= MAX_AUTO_REFUND:
        return {
            "allowed": True,
            "reason": f"Amount ${amount:.2f} is within auto-approval limit (${MAX_AUTO_REFUND:.2f})",
        }

    return {
        "allowed": False,
        "reason": (
            f"Amount ${amount:.2f} exceeds auto-approval limit (${MAX_AUTO_REFUND:.2f}). Human approval required."
        ),
    }


def check_action_permission(action: str, context: dict | None = None) -> dict:
    """
    General permission check for any agent action.

    Extend this function as you add more sensitive operations.
    """
    blocked_actions = {"delete_account", "modify_billing", "access_payment_info"}

    if action in blocked_actions:
        return {
            "allowed": False,
            "reason": f"Action '{action}' is not permitted for automated agents. Requires human agent.",
        }

    return {"allowed": True, "reason": "Action permitted"}
