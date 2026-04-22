"""
Support agent — the main ReAct agent with tool calling.

This is the core of the system. It receives a classified intent,
binds the appropriate tools, and runs a ReAct loop:
  Reason → Act (call tool) -> Observe (read result) -> Reason again

Uses LangChain's native .bind_tools() for function calling
and LangGraph's ToolNode for automatic tool execution.
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage

from src.models import WorkflowState
from src.utils.llm import get_llm
from src.tools import ALL_TOOLS


SYSTEM_PROMPT = """\
You are a helpful, professional customer support agent for TechGear — an online electronics retailer.

Your responsibilities:
1. Identify the customer (look them up by email or ID if provided)
2. Understand their issue fully before taking action
3. Use the available tools to look up orders, check statuses, search the knowledge base, and resolve issues
4. For refunds: ALWAYS check eligibility first, then process if eligible
5. Create a support ticket for every interaction
6. Send confirmation emails for important actions (refunds, resolutions)

Guidelines:
- Be warm, empathetic, and professional
- Never make up information — always use tools to verify
- If you cannot resolve an issue, escalate honestly
- Never ask for sensitive information (SSN, full credit card numbers)
- For refunds over $50, inform the customer that manager approval is needed
- Always confirm actions before taking them

You have access to the customer's conversation history. Use it for context.
"""


def support_agent(state: WorkflowState) -> WorkflowState:
    """
    LangGraph node: the main support agent.

    Runs one step of the ReAct loop — reasons about the conversation
    and either responds to the customer or calls a tool.
    The graph handles the loop: if the agent calls a tool, the
    ToolNode executes it and control returns here.
    """
    llm = get_llm().bind_tools(ALL_TOOLS)

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="messages"),
    ])

    chain = prompt | llm

    response = chain.invoke({"messages": state.messages})

    # Track tool calls for observability
    if response.tool_calls:
        for tc in response.tool_calls:
            tool_name = tc["name"]
            state.tool_calls_made.append(tool_name)
            print(f"  [Agent] Calling tool: {tool_name}")

    state.messages.append(response)
    return state


def should_continue_or_respond(state: WorkflowState) -> str:
    """
    Conditional edge: after the agent node, check if it called tools
    or produced a final response.

    If the last message has tool_calls → go to 'tools' node
    If the last message is a plain response → go to 'respond'
    """
    last_message = state.messages[-1]

    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"

    return "respond"
