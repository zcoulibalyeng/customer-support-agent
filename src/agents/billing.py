"""
Billing agent — handles refund evaluation and human-in-the-loop approval.

When a refund exceeds the auto-approval threshold, this agent
prepares the refund proposal and triggers a LangGraph interrupt
to pause for human review.
"""

from langchain_core.messages import AIMessage

from src.models import WorkflowState
from src.guardrails.permissions import check_refund_permission


def evaluate_refund(state: WorkflowState) -> WorkflowState:
    """
    LangGraph node: evaluate whether a refund needs human approval.

    Reads the refund amount from state (set by the support agent
    after calling check_refund_eligibility) and decides whether
    to auto-approve or flag for human review.
    """
    if state.refund_amount is None:
        return state

    permission = check_refund_permission(state.refund_amount)

    if permission["allowed"]:
        # Auto-approved — proceed
        state.needs_human_approval = False
        state.refund_approved = True
        print(f"  [Billing] Refund ${state.refund_amount:.2f} auto-approved")
    else:
        # Needs human review
        state.needs_human_approval = True
        state.refund_approved = None  # Pending
        print(f"  [Billing] Refund ${state.refund_amount:.2f} requires human approval")

    return state
