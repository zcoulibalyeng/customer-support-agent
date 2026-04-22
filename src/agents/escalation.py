"""
Escalation agent — handles handoff to human support agents.

When the AI agent cannot resolve an issue (low confidence, customer
frustration, or complex issue), this node prepares a context summary
and marks the conversation for human takeover.
"""

from langchain_core.messages import AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from src.models import WorkflowState
from src.utils.llm import get_llm

SUMMARY_PROMPT = """\
You are preparing a handoff summary for a human support agent.

Review the conversation history and produce a concise summary including:
1. Customer name and ID (if known)
2. What the customer's issue is
3. What has been tried so far
4. Why the AI agent could not resolve this
5. Suggested next steps for the human agent

Be factual and concise. The human agent will read this before picking up the conversation.
"""


def escalate_to_human(state: WorkflowState) -> WorkflowState:
    """
    LangGraph node: prepare escalation context and mark for human handoff.

    Generates a summary of the conversation for the human agent
    and updates the state to indicate escalation.
    """
    llm = get_llm()

    chain = (
        ChatPromptTemplate.from_messages(
            [
                ("system", SUMMARY_PROMPT),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
        | llm
        | StrOutputParser()
    )

    summary = chain.invoke({"messages": state.messages})

    state.is_escalated = True
    state.messages.append(
        AIMessage(
            content=(
                "I want to make sure you get the best help possible. "
                "I'm connecting you with a human support specialist who can assist further. "
                "I've prepared a summary of our conversation so you won't need to repeat anything. "
                "A team member will be with you shortly. Thank you for your patience."
            )
        )
    )

    print("  [Escalation] Conversation escalated to human agent")
    print(f"  [Escalation] Summary:\n{summary[:300]}...")

    return state
