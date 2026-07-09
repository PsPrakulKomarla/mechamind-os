from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.db.database import get_db
from app.db.models import ChatSession, ChatMessage, UserFeedback
from app.models.schemas import (
    ChatSessionCreate, ChatSessionUpdate, ChatSessionResponse,
    ChatMessageCreate, ChatMessageResponse,
    ChatRequest, ChatResponse, ChatStreamChunk,
    FeedbackCreate, FeedbackResponse
)
from app.services.rag.chain import RAGChain
from app.services.rag.llm_provider import LLMProviderFactory
from app.core.config import settings

router = APIRouter()


@router.post("/sessions", response_model=ChatSessionResponse, status_code=201)
async def create_session(
    session: ChatSessionCreate,
    db: AsyncSession = Depends(get_db),
):
    # TODO: Get user_id from auth
    user_id = UUID("00000000-0000-0000-0000-000000000000")  # placeholder
    
    new_session = ChatSession(
        user_id=user_id,
        title=session.title or "New Conversation",
        context=session.context or {},
    )
    
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    
    return new_session


@router.get("/sessions", response_model=List[ChatSessionResponse])
async def list_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    # TODO: Filter by user_id from auth
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.is_active == True)
        .order_by(desc(ChatSession.updated_at))
        .offset(skip)
        .limit(limit)
    )
    sessions = result.scalars().all()
    
    return sessions


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session


@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
async def get_session_messages(
    session_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
        .offset(skip)
        .limit(limit)
    )
    messages = result.scalars().all()
    
    return messages


@router.patch("/sessions/{session_id}", response_model=ChatSessionResponse)
async def update_session(
    session_id: UUID,
    update: ChatSessionUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(session, field, value)
    
    session.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(session)
    
    return session


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session.is_active = False
    await db.commit()
    
    return {"message": "Session deleted"}


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    # Get or create session
    if request.session_id:
        result = await db.execute(select(ChatSession).where(ChatSession.id == request.session_id))
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
    else:
        session = ChatSession(
            user_id=UUID("00000000-0000-0000-0000-000000000000"),
            title=request.message[:50] + "..." if len(request.message) > 50 else request.message,
            context=request.context or {},
        )
        db.add(session)
        await db.flush()
    
    # Save user message
    user_message = ChatMessage(
        session_id=session.id,
        role="user",
        content=request.message,
        metadata=request.context or {},
    )
    db.add(user_message)
    
    # Get relevant context from RAG
    rag_chain = RAGChain()
    rag_result = await rag_chain.query(
        question=request.message,
        context=request.context,
        equipment_id=request.equipment_id,
        top_k=request.top_k or settings.TOP_K_RESULTS,
    )
    
    # Generate response
    llm = LLMProviderFactory.get_provider()
    
    # Build context from RAG results
    context_text = "\n\n".join([
        f"Source: {c['source']}\n{c['content']}"
        for c in rag_result.get("chunks", [])
    ])
    
    system_prompt = f"""You are an expert industrial knowledge assistant for Mechamind OS.
You help engineers, operators, and maintenance personnel with questions about equipment, procedures, and operations.

Use the following context to answer the user's question. Cite your sources clearly.
If the context doesn't contain enough information, say so and provide general guidance based on your training.

Context:
{context_text}

Guidelines:
- Be precise and technical
- Always cite sources when using context
- If unsure, say so rather than guessing
- Prioritize safety in all responses
- Reference equipment tags, procedures, and standards when relevant"""
    
    messages = [
        {"role": "system", "content": system_prompt},
    ]
    
    # Add recent conversation history
    history_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
        .order_by(desc(ChatMessage.created_at))
        .limit(10)
    )
    history = list(reversed(history_result.scalars().all()))
    
    for msg in history:
        if msg.role in ("user", "assistant"):
            messages.append({"role": msg.role, "content": msg.content})
    
    # Add current question
    messages.append({"role": "user", "content": request.message})
    
    # Stream response
    response_content = ""
    citations = []
    
    async for chunk in llm.stream_chat(messages, temperature=0.1):
        response_content += chunk
    
    # Add citations
    for i, c in enumerate(rag_result.get("chunks", [])):
        citations.append({
            "document_id": c.get("document_id"),
            "chunk_id": c.get("chunk_id"),
            "excerpt": c.get("content", "")[:200],
            "score": c.get("score"),
            "source": c.get("source"),
        })
    
    # Save assistant message
    assistant_message = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=response_content,
        citations=citations,
        metadata={
            "model": settings.DEFAULT_LLM_PROVIDER,
            "rag_chunks_used": len(rag_result.get("chunks", [])),
        },
    )
    db.add(assistant_message)
    
    session.updated_at = datetime.utcnow()
    await db.commit()
    
    return ChatResponse(
        message=assistant_message,
        session_id=session.id,
        citations=citations,
        rag_context=rag_result,
    )


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    from fastapi.responses import StreamingResponse
    import json
    
    # Similar to chat but streaming
    async def generate():
        # Implementation for streaming response
        yield f"data: {json.dumps({'type': 'start', 'session_id': str(request.session_id)})}\n\n"
        # ... stream chunks
        yield f"data: {json.dumps({'type': 'end'})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    feedback: FeedbackCreate,
    db: AsyncSession = Depends(get_db),
):
    # TODO: Get user_id from auth
    user_id = UUID("00000000-0000-0000-0000-000000000000")
    
    new_feedback = UserFeedback(
        user_id=user_id,
        message_id=feedback.message_id,
        rating=feedback.rating,
        feedback_text=feedback.feedback_text,
        vote=feedback.vote,
        metadata=feedback.metadata or {},
    )
    
    db.add(new_feedback)
    await db.commit()
    await db.refresh(new_feedback)
    
    return new_feedback


@router.get("/sessions/{session_id}/export")
async def export_session(
    session_id: UUID,
    format: str = Query("json", pattern="^(json|markdown|txt)$"),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    )
    messages = messages_result.scalars().all()
    
    if format == "markdown":
        content = f"# {session.title}\n\n"
        for msg in messages:
            role = "**User**" if msg.role == "user" else "**Assistant**"
            content += f"{role} ({msg.created_at.strftime('%Y-%m-%d %H:%M')}):\n{msg.content}\n\n"
            if msg.citations:
                content += "*Sources:*\n"
                for c in msg.citations:
                    content += f"- {c.get('excerpt', '')[:100]}...\n"
                content += "\n"
        return {"content": content, "format": "markdown"}
    
    elif format == "txt":
        content = f"{session.title}\n{'='*50}\n\n"
        for msg in messages:
            role = "User" if msg.role == "user" else "Assistant"
            content += f"[{msg.created_at.strftime('%Y-%m-%d %H:%M')}] {role}:\n{msg.content}\n\n"
        return {"content": content, "format": "txt"}
    
    return {
        "session": session,
        "messages": messages,
    }