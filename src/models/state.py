"""
State models for the LangGraph workflow.

WorkflowState is the single object that flows through every node.
Sub-models define structured outputs from LLM calls.
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Optional

from pydantic import BaseModel, Field
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Intent(str, Enum):
    """Customer intent categories."""
    ORDER_STATUS = "order_status"
    REFUND_REQUEST = "refund_request"
    TECHNICAL_SUPPORT = "technical_support"
    BILLING_QUESTION = "billing_question"
    ACCOUNT_INQUIRY = "account_inquiry"
    GENERAL_QUESTION = "general_question"
    ESCALATE = "escalate"


class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


# ---------------------------------------------------------------------------
# Structured output models (used with .with_structured_output())
# ---------------------------------------------------------------------------

class IntentClassification(BaseModel):
    """Output from the classifier agent."""
    intent: Intent = Field(description="The classified intent of the customer message")
    confidence: float = Field(description="Confidence score between 0 and 1")
    reasoning: str = Field(description="Brief explanation of why this intent was chosen")
    priority: TicketPriority = Field(description="Suggested ticket priority")


class RefundDecision(BaseModel):
    """Output from the refund evaluation."""
    should_refund: bool = Field(description="Whether a refund should be issued")
    amount: float = Field(description="The refund amount in dollars")
    reason: str = Field(description="Explanation for the decision")
    requires_approval: bool = Field(description="Whether human approval is needed")


class EscalationDecision(BaseModel):
    """Output when the agent decides to escalate."""
    reason: str = Field(description="Why the agent cannot handle this")
    suggested_department: str = Field(description="Which team should handle this")
    context_summary: str = Field(description="Summary for the human agent")


# ---------------------------------------------------------------------------
# Graph state
# ---------------------------------------------------------------------------

class WorkflowState(BaseModel):
    """
    Central state object for the support agent graph.

    Every node reads from and writes to this state.
    The `messages` field uses LangGraph's add_messages reducer
    to automatically append new messages to the conversation history.
    """

    # --- Conversation ---
    messages: Annotated[list[BaseMessage], add_messages] = Field(default_factory=list)

    # --- Customer context ---
    customer_id: Optional[str] = Field(default=None)
    customer_email: Optional[str] = Field(default=None)
    customer_name: Optional[str] = Field(default=None)

    # --- Classification ---
    intent: Optional[Intent] = Field(default=None)
    priority: Optional[TicketPriority] = Field(default=None)
    confidence: Optional[float] = Field(default=None)

    # --- Ticket ---
    ticket_id: Optional[str] = Field(default=None)

    # --- Refund (populated when intent is refund_request) ---
    refund_order_id: Optional[str] = Field(default=None)
    refund_amount: Optional[float] = Field(default=None)
    refund_approved: Optional[bool] = Field(default=None)

    # --- Control flow ---
    needs_human_approval: bool = Field(default=False)
    is_escalated: bool = Field(default=False)
    is_resolved: bool = Field(default=False)

    # --- Metadata ---
    tool_calls_made: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True
