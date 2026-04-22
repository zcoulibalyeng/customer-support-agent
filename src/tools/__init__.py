from .customers import lookup_customer, lookup_customer_by_id
from .email import send_email
from .knowledge import search_knowledge_base
from .orders import get_customer_orders, get_order_for_refund, get_order_status
from .refunds import check_refund_eligibility, process_refund, request_refund_approval
from .tickets import close_ticket, create_ticket, get_customer_tickets, update_ticket

ALL_TOOLS = [
    # Customer
    lookup_customer,
    lookup_customer_by_id,
    # Orders
    get_order_status,
    get_customer_orders,
    get_order_for_refund,
    # Tickets
    create_ticket,
    update_ticket,
    close_ticket,
    get_customer_tickets,
    # Refunds
    check_refund_eligibility,
    process_refund,
    request_refund_approval,
    # Knowledge
    search_knowledge_base,
    # Email
    send_email,
]
