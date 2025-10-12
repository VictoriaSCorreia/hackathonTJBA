from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Optional
from sqlalchemy.orm import Session

from app.api.deps import get_current_guest, get_db
from app.schemas.conversation import (
    ConversationCreate,
    ConversationRead,
    ConversationWithMessages,
    MessageCreate,
    MessageRead,
)
from app.services.conversation_service import ConversationService
from app.services.legal_agent import (
    generate_clarify_questions,
    generate_final_answer,
    parse_q123,
)


router = APIRouter()


@router.post("/conversations", response_model=ConversationRead, status_code=201)
def create_conversation(
    payload: Optional[ConversationCreate] = Body(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_guest),
):
    service = ConversationService(db)
    title = payload.title if payload and getattr(payload, "title", None) else None
    conv = service.create_conversation(guest_id=current_user.guest_id, title=title)
    return conv


@router.get("/conversations", response_model=list[ConversationRead])
def list_conversations(db: Session = Depends(get_db), current_user=Depends(get_current_guest)):
    service = ConversationService(db)
    return service.list_conversations(guest_id=current_user.guest_id)


@router.get("/conversations/{conversation_id}", response_model=ConversationWithMessages)
def get_conversation(conversation_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_guest)):
    service = ConversationService(db)
    conv = service.get_conversation(conversation_id, guest_id=current_user.guest_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    messages = service.list_messages(conversation_id=conv.id)
    return {
        "conversation": conv,
        "messages": messages,
    }


@router.post("/conversations/{conversation_id}/messages", response_model=MessageRead)
def post_message(
    conversation_id: int,
    payload: MessageCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_guest),
):
    # Validate conversation ownership
    service = ConversationService(db)
    conv = service.get_conversation(conversation_id, guest_id=current_user.guest_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Save message
    saved_msg = service.add_message(conversation_id=conv.id, role=payload.role, content=payload.content)

    # Only trigger agent when role=user
    if payload.role == "user":
        # Load history to detect clarify/final stage
        history = service.list_messages(conversation_id=conv.id)
        # Find the last assistant message before this one
        last_assistant = None
        for m in reversed(history):
            if m.role == "assistant":
                last_assistant = m
                break

        if last_assistant and isinstance(last_assistant.content, str) and last_assistant.content.strip().startswith("<clarify>"):
            # Stage B: user answered Q1–Q3 -> produce final answer
            # U0 = last user message before the clarify block
            U0 = ""
            for m in reversed(history):
                if m.id == last_assistant.id:
                    # skip messages after clarify
                    continue
                if m.created_at >= last_assistant.created_at:
                    continue
                if m.role == "user":
                    U0 = m.content
                    break
            if not U0:
                # fallback to first user message in history
                for m in history:
                    if m.role == "user":
                        U0 = m.content
                        break

            Qs = parse_q123(last_assistant.content)
            U1 = payload.content

            # Simple heuristic: if user changed subject entirely, start a new Clarify stage
            try:
                from app.services.legal_agent import is_new_topic  # local import to avoid cycles

                if is_new_topic(U0, Qs, U1):
                    clarify_block = generate_clarify_questions(user_message=U1, k=5)
                    assistant_msg = service.add_message(conversation_id=conv.id, role="assistant", content=clarify_block)
                    return assistant_msg
            except Exception:
                # If heuristic fails, continue with final answer normally
                pass

            # Reduz k para acelerar RAG e resposta final
            final = generate_final_answer(U0=U0, Qs=Qs, U1=U1, conversation_id=str(conv.id), k=3)
            assistant_text = final.get("text", "")
            assistant_msg = service.add_message(conversation_id=conv.id, role="assistant", content=assistant_text)
            return assistant_msg
        else:
            # Stage A: first pass -> generate 3 clarify questions
            # Reduz k para acelerar primeira resposta
            clarify_block = generate_clarify_questions(user_message=payload.content, k=3)
            assistant_msg = service.add_message(conversation_id=conv.id, role="assistant", content=clarify_block)
            return assistant_msg
    return saved_msg
