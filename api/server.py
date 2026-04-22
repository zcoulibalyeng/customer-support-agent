"""
FastAPI REST + WebSocket API for the support agent.

Endpoints:
    POST   /chat              Send a message and get a response
    GET    /chat/session       Create a new chat session
    GET    /health             Health check
Usage:
    uvicorn api.server:app --reload --port 8000
"""

from __future__ import annotations

from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

from src.tools.knowledge import init_knowledge_base
from src.utils.database import init_database
from src.workflow.runner import create_session, send_message

app = FastAPI(
    title="TechGear Customer Support Agent API",
    description="AI-powered customer support with tool calling, RAG, and human-in-the-loop.",
    version="1.0.0",
)


@app.on_event("startup")
async def startup():
    init_database()
    init_knowledge_base()


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class ChatRequest(BaseModel):
    message: str = Field(description="Customer message")
    thread_id: str = Field(description="Conversation session ID")
    customer_email: Optional[str] = Field(default=None, description="Customer email for lookup")


class ChatResponse(BaseModel):
    response: str
    thread_id: str


class SessionResponse(BaseModel):
    thread_id: str


# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------


@app.get("/health")
async def health():
    return {"status": "healthy", "agent": "TechGear Support"}


@app.get("/chat/session", response_model=SessionResponse)
async def new_session():
    """Create a new chat session."""
    return SessionResponse(thread_id=create_session())


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message and get the agent's response."""
    response = send_message(
        message=request.message,
        thread_id=request.thread_id,
        customer_email=request.customer_email,
    )
    return ChatResponse(response=response, thread_id=request.thread_id)
