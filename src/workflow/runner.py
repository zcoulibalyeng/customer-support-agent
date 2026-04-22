"""
Workflow runner — manages sessions, invokes the graph, and handles output.

Each customer conversation gets a unique thread_id for memory persistence.
The runner handles the conversion between user input strings and the
full WorkflowState that the graph expects.
"""

from __future__ import annotations

import uuid

from langchain_core.messages import HumanMessage, AIMessage

from src.models import WorkflowState
from src.workflow.graph import get_graph
from src.utils.database import init_database
from src.tools.knowledge import init_knowledge_base


def _ensure_initialised():
    """Initialise database and knowledge base on first run."""
    init_database()
    init_knowledge_base()


def create_session() -> str:
    """Create a new conversation session. Returns a thread_id."""
    return str(uuid.uuid4())


def send_message(
    message: str,
    thread_id: str,
    customer_email: str | None = None,
) -> str:
    """
    Send a customer message through the support agent graph.

    Args:
        message:        The customer's message text.
        thread_id:      Conversation session ID (for memory persistence).
        customer_email: Optional customer email for identification.

    Returns:
        The agent's response text.
    """
    _ensure_initialised()

    graph = get_graph()

    # Build input state
    input_state = {
        "messages": [HumanMessage(content=message)],
    }

    if customer_email:
        input_state["customer_email"] = customer_email

    # Config with thread_id for memory checkpointing
    config = {"configurable": {"thread_id": thread_id}}

    print(f"\n{'=' * 60}")
    print(f"  Customer: {message}")
    print("=" * 60)

    # Run the graph
    result = graph.invoke(input_state, config=config)

    # Extract the last AI message as the response
    response_text = ""
    if isinstance(result, dict) and "messages" in result:
        for msg in reversed(result["messages"]):
            if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
                response_text = msg.content
                break

    print(f"\n  Agent: {response_text[:200]}{'...' if len(response_text) > 200 else ''}")

    return response_text


def run_interactive():
    """
    Run an interactive CLI chat session.

    Creates a new session and loops until the user types 'quit'.
    """
    _ensure_initialised()

    thread_id = create_session()
    print("\n" + "=" * 60)
    print("  TechGear Customer Support Agent")
    print("  Type your message or 'quit' to exit")
    print("=" * 60)

    customer_email = input("\n  Your email (optional, press Enter to skip): ").strip() or None

    while True:
        user_input = input("\n  You: ").strip()

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("\n  Thank you for contacting TechGear support. Goodbye!")
            break

        response = send_message(user_input, thread_id, customer_email)
        print(f"\n  Agent: {response}")
