"""
End-to-end workflow test — runs full conversations through the graph.
"""

from dotenv import load_dotenv

from src.tools.knowledge import init_knowledge_base
from src.utils.database import init_database
from src.workflow.runner import create_session, send_message

load_dotenv()


def test_order_inquiry():
    print("\n  TEST: Order status inquiry (e2e)")
    init_database()
    init_knowledge_base()

    thread_id = create_session()
    response = send_message(
        "Hi, I'm alice@example.com. Where is my order ORD-1001?",
        thread_id,
        customer_email="alice@example.com",
    )

    assert response, "Agent should produce a response"
    assert len(response) > 20, "Response should be substantive"
    print("  ✅ Order inquiry handled")
    print(f"  Response preview: {response[:150]}...")


def test_troubleshooting():
    print("\n  TEST: Technical support (e2e)")
    init_database()
    init_knowledge_base()

    thread_id = create_session()
    response = send_message(
        "My wireless headphones won't charge. I've tried different cables.",
        thread_id,
    )

    assert response, "Agent should produce a response"
    print("  ✅ Troubleshooting handled")
    print(f"  Response preview: {response[:150]}...")


def test_multi_turn_conversation():
    print("\n  TEST: Multi-turn conversation (e2e)")
    init_database()
    init_knowledge_base()

    thread_id = create_session()

    r1 = send_message("Hi, I'm alice@example.com", thread_id, customer_email="alice@example.com")
    assert r1, "First response should exist"
    print(f"  Turn 1: {r1[:80]}...")

    r2 = send_message("Can you show me my orders?", thread_id)
    assert r2, "Second response should exist"
    print(f"  Turn 2: {r2[:80]}...")

    print("  ✅ Multi-turn conversation works with memory")


if __name__ == "__main__":
    print("=" * 60)
    print("  END-TO-END WORKFLOW TESTS")
    print("=" * 60)
    test_order_inquiry()
    test_troubleshooting()
    test_multi_turn_conversation()
    print("\n  ✅ All workflow tests passed")
