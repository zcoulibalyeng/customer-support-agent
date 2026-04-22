"""
Tests for the intent classifier.
"""

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from src.agents.classifier import classify_intent
from src.models import Intent, WorkflowState

load_dotenv()


def test_classify_order_status():
    state = WorkflowState(messages=[HumanMessage(content="Where is my order ORD-1001?")])
    result = classify_intent(state)
    assert result.intent == Intent.ORDER_STATUS
    print("  ✅ Order status classified correctly")


def test_classify_refund():
    state = WorkflowState(messages=[HumanMessage(content="I want a refund for my headphones")])
    result = classify_intent(state)
    assert result.intent == Intent.REFUND_REQUEST
    print("  ✅ Refund request classified correctly")


def test_classify_technical():
    state = WorkflowState(messages=[HumanMessage(content="My headphones won't charge")])
    result = classify_intent(state)
    assert result.intent == Intent.TECHNICAL_SUPPORT
    print("  ✅ Technical support classified correctly")


def test_classify_billing():
    state = WorkflowState(messages=[HumanMessage(content="I was charged twice on my credit card")])
    result = classify_intent(state)
    assert result.intent == Intent.BILLING_QUESTION
    print("  ✅ Billing question classified correctly")


if __name__ == "__main__":
    print("=" * 60)
    print("  CLASSIFIER TESTS")
    print("=" * 60)
    test_classify_order_status()
    test_classify_refund()
    test_classify_technical()
    test_classify_billing()
    print("\n  ✅ All classifier tests passed")
