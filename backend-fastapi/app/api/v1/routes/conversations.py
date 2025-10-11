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
from app.services.legal_agent import rag_retrieve, call_model


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

    # Save user message
    user_msg = service.add_message(conversation_id=conv.id, role=payload.role, content=payload.content)

    # Call agent only when role=user
    if payload.role == "user":
        documents = rag_retrieve(payload.content, k=5)
        model_resp = call_model(user_message=payload.content, conversation_id=str(conv.id), documents=documents)
        assistant_text = model_resp.get("text", "")
        assistant_msg = service.add_message(conversation_id=conv.id, role="assistant", content=assistant_text)
        return assistant_msg

    return user_msg
