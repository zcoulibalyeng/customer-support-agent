"""
Streamlit chat UI for the TechGear Customer Support Agent.

Usage:
    streamlit run ui/chat.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from src.workflow.runner import send_message, create_session
from src.utils.database import init_database
from src.tools.knowledge import init_knowledge_base


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

st.set_page_config(page_title="TechGear Support", page_icon="🛒", layout="centered")

if "initialised" not in st.session_state:
    init_database()
    init_knowledge_base()
    st.session_state.initialised = True

if "thread_id" not in st.session_state:
    st.session_state.thread_id = create_session()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "customer_email" not in st.session_state:
    st.session_state.customer_email = None


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("TechGear Support")
    st.caption(f"Session: `{st.session_state.thread_id[:8]}...`")

    email = st.text_input("Your email (optional)", value=st.session_state.customer_email or "")
    if email:
        st.session_state.customer_email = email

    st.divider()
    st.markdown("**Test customers:**")
    st.code("alice@example.com\nbob@example.com\ncarol@example.com")

    st.divider()
    if st.button("New conversation"):
        st.session_state.thread_id = create_session()
        st.session_state.messages = []
        st.rerun()


# ---------------------------------------------------------------------------
# Chat interface
# ---------------------------------------------------------------------------

st.title("🛒 TechGear Customer Support")

# Display conversation history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Chat input
if user_input := st.chat_input("How can we help you today?"):
    # Display user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # Get agent response
    with st.chat_message("assistant"):
        with st.spinner("Looking into this..."):
            response = send_message(
                message=user_input,
                thread_id=st.session_state.thread_id,
                customer_email=st.session_state.customer_email,
            )
        st.write(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
