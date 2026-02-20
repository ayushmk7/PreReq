"""Chat API endpoints for the agentic AI assistant.

Supports multi-turn conversations with persistent sessions.
The assistant uses OpenAI function calling to query and act
on the full ConceptLens system.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.models import ChatMessage, ChatSession, Exam
from app.schemas.schemas import (
    ChatMessageResponse,
    ChatSendRequest,
    ChatSendResponse,
    ChatSessionCreate,
    ChatSessionResponse,
)
from app.services.chat_service import run_agent_turn

logger = logging.getLogger("conceptlens.chat")

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/sessions", response_model=ChatSessionResponse)
async def create_session(
    body: ChatSessionCreate,
    db: AsyncSession = Depends(get_db),
    _user: str = "instructor",
):
    """Create a new chat session, optionally scoped to an exam."""
    if body.exam_id:
        exam = await db.get(Exam, body.exam_id)
        if not exam:
            raise HTTPException(status_code=404, detail="Exam not found")

    session = ChatSession(
        exam_id=body.exam_id,
        title=body.title or None,
        created_by=_user,
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)
    return session


@router.get("/sessions", response_model=list[ChatSessionResponse])
async def list_sessions(
    exam_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List all chat sessions, optionally filtered by exam."""
    q = select(ChatSession).order_by(ChatSession.updated_at.desc())
    if exam_id:
        q = q.where(ChatSession.exam_id == exam_id)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a chat session by ID."""
    session = await db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return session


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageResponse])
async def get_messages(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get all messages in a chat session."""
    session = await db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    )
    messages = result.scalars().all()
    return [
        ChatMessageResponse(
            id=m.id,
            role=m.role,
            content=m.content,
            tool_calls=m.tool_calls_json,
            tool_name=m.tool_name,
            created_at=m.created_at,
        )
        for m in messages
        if m.role in ("user", "assistant")
    ]


@router.post("/sessions/{session_id}/messages", response_model=ChatSendResponse)
async def send_message(
    session_id: UUID,
    body: ChatSendRequest,
    db: AsyncSession = Depends(get_db),
):
    """Send a message to the AI assistant in an existing session."""
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.id == session_id)
        .options(selectinload(ChatSession.messages))
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    if body.exam_id and body.exam_id != session.exam_id:
        session.exam_id = body.exam_id

    assistant_text, tools_called = await run_agent_turn(session, body.message, db)

    if not session.title and body.message:
        session.title = body.message[:80]

    return ChatSendResponse(
        session_id=session.id,
        assistant_message=assistant_text,
        tool_calls_made=tools_called,
    )


@router.post("/quick", response_model=ChatSendResponse)
async def quick_chat(
    body: ChatSendRequest,
    db: AsyncSession = Depends(get_db),
    _user: str = "instructor",
):
    """One-shot chat: creates a session and sends a message in one call."""
    session = ChatSession(
        exam_id=body.exam_id,
        title=body.message[:80] if body.message else None,
        created_by=_user,
    )
    db.add(session)
    await db.flush()

    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.id == session.id)
        .options(selectinload(ChatSession.messages))
    )
    session = result.scalar_one_or_none()

    assistant_text, tools_called = await run_agent_turn(session, body.message, db)

    return ChatSendResponse(
        session_id=session.id,
        assistant_message=assistant_text,
        tool_calls_made=tools_called,
    )


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a chat session and all its messages."""
    session = await db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    await db.delete(session)
    await db.flush()
    return {"status": "deleted"}
