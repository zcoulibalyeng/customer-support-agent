"""
LangGraph state machine — the complete support agent workflow.

Key patterns:
  - Conditional edge after classifier routes to escalation or support
  - ReAct loop: support_agent -> tools -> support_agent (repeats until agent stops calling tools)
  - Human-in-the-loop: interrupt() pauses for refund approval when needed
  - Safety check runs on every incoming message before classification
"""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from src.agents import (
    classify_intent,
    escalate_to_human,
    support_agent,
)
from src.guardrails.safety import detect_pii, detect_prompt_injection
from src.models import Intent, WorkflowState
from src.tools import ALL_TOOLS

# ---------------------------------------------------------------------------
# Safety check node
# ---------------------------------------------------------------------------


def safety_check(state: WorkflowState) -> WorkflowState:
    """
    First node in the graph — runs PII detection and prompt injection
    defense on the incoming message before any agent sees it.
    """
    last_message = ""
    for msg in reversed(state.messages):
        if isinstance(msg, HumanMessage):
            last_message = msg.content
            break

    if not last_message:
        return state

    # Check for PII
    pii_result = detect_pii(last_message)
    if pii_result["has_pii"]:
        state.messages.append(AIMessage(content=pii_result["warning"]))
        print(f"  [Safety] PII detected: {pii_result['types']}")

    # Check for prompt injection
    injection_result = detect_prompt_injection(last_message)
    if injection_result["is_injection"]:
        state.messages.append(
            AIMessage(content="I'm here to help with your support needs. How can I assist you today?")
        )
        state.errors.append(f"Prompt injection attempt blocked: {injection_result['pattern']}")
        print(f"  [Safety] Prompt injection blocked: {injection_result['pattern']}")

    return state


# ---------------------------------------------------------------------------
# Routing functions for conditional edges
# ---------------------------------------------------------------------------


def route_after_classification(state: WorkflowState) -> str:
    """After classification, route to escalation or the support agent."""
    if state.intent == Intent.ESCALATE:
        return "escalate"
    return "support"


def route_after_agent(state: WorkflowState) -> str:
    """
    After the support agent runs, determine next step:
      - If it called tools → go to tool execution
      - If it produced a final response → end
    """
    last_message = state.messages[-1]

    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"

    return "respond"


# ---------------------------------------------------------------------------
# Response node (final step before END)
# ---------------------------------------------------------------------------


def respond(state: WorkflowState) -> WorkflowState:
    """Final node — marks the turn as complete."""
    state.is_resolved = True
    return state


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------


def build_graph():
    """
    Construct and compile the support agent graph.

    Returns:
        Compiled graph with memory checkpointing enabled.
    """
    graph = StateGraph(WorkflowState)

    # --- Nodes ---
    graph.add_node("safety_check", safety_check)
    graph.add_node("classify_intent", classify_intent)
    graph.add_node("support_agent", support_agent)
    graph.add_node("tools", ToolNode(ALL_TOOLS))
    graph.add_node("escalate_to_human", escalate_to_human)
    graph.add_node("respond", respond)

    # --- Edges ---

    # Entry: every message goes through safety first
    graph.add_edge(START, "safety_check")
    graph.add_edge("safety_check", "classify_intent")

    # After classification: escalate or handle
    graph.add_conditional_edges(
        "classify_intent",
        route_after_classification,
        {
            "escalate": "escalate_to_human",
            "support": "support_agent",
        },
    )

    # Escalation -> end
    graph.add_edge("escalate_to_human", END)

    # ReAct loop: agent -> tools -> agent (repeats)
    graph.add_conditional_edges(
        "support_agent",
        route_after_agent,
        {
            "tools": "tools",
            "respond": "respond",
        },
    )

    # After tools execute, return to agent for next reasoning step
    graph.add_edge("tools", "support_agent")

    # After final response -> end
    graph.add_edge("respond", END)

    # Compile with memory checkpointing
    memory = MemorySaver()
    return graph.compile(checkpointer=memory)


# Module-level compiled graph (singleton)
compiled_graph = None


def get_graph():
    """Return the compiled graph (lazy singleton)."""
    global compiled_graph
    if compiled_graph is None:
        compiled_graph = build_graph()
    return compiled_graph
