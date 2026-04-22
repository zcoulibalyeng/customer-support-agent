"""
Classifier agent — determines customer intent from their message.

Uses .with_structured_output(IntentClassification) to guarantee
a typed classification result. This feeds into the graph's
conditional edges for routing to the correct handler.
"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage

from src.models import WorkflowState, IntentClassification
from src.utils.llm import get_llm


SYSTEM_PROMPT = """\
You are a customer support intent classifier.

Classify the customer's message into exactly one intent:
- order_status: Customer asking about where their order is, tracking, delivery
- refund_request: Customer wants money back, return, exchange
- technical_support: Product not working, troubleshooting, setup help
- billing_question: Charges, invoices, subscription, payment issues
- account_inquiry: Account settings, profile, plan changes
- general_question: Product questions, pre-purchase, anything else
- escalate: Customer is very frustrated, threatening, or the issue is too complex

Also assess the priority:
- low: General question, no urgency
- medium: Standard support request
- high: Customer is frustrated or issue impacts their work
- urgent: System down, security concern, or customer threatening to leave

Be accurate. A wrong classification sends the customer to the wrong team.
"""


def classify_intent(state: WorkflowState) -> WorkflowState:
    """
    LangGraph node: classify the customer's intent.

    Reads the last human message and produces a structured classification.
    """
    llm = get_llm().with_structured_output(IntentClassification)

    chain = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{message}"),
    ]) | llm

    # Get the last human message
    last_message = ""
    for msg in reversed(state.messages):
        if isinstance(msg, HumanMessage):
            last_message = msg.content
            break

    result: IntentClassification = chain.invoke({"message": last_message})

    state.intent = result.intent
    state.priority = result.priority
    state.confidence = result.confidence

    print(f"  [Classifier] Intent: {result.intent.value} | Priority: {result.priority.value} | Confidence: {result.confidence:.2f}")
    print(f"  [Classifier] Reasoning: {result.reasoning}")

    return state
