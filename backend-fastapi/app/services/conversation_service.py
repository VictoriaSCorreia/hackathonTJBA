from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session
from sqlmodel import select

from app.models.conversation import Conversation, Message


class ConversationService:
    def __init__(self, db: Session):
        self.db = db

    # Conversations
    def create_conversation(self, guest_id: str, title: Optional[str]) -> Conversation:
        conv = Conversation(guest_id=guest_id, title=title)
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(conv)
        return conv

    def list_conversations(self, guest_id: str) -> List[Conversation]:
        stmt = select(Conversation).where(Conversation.guest_id == guest_id).order_by(Conversation.created_at.desc())
        return list(self.db.scalars(stmt))

    def get_conversation(self, conv_id: int, guest_id: str) -> Optional[Conversation]:
        stmt = select(Conversation).where(Conversation.id == conv_id, Conversation.guest_id == guest_id)
        return self.db.scalar(stmt)

    # Messages
    def add_message(self, conversation_id: int, role: str, content: str) -> Message:
        msg = Message(conversation_id=conversation_id, role=role, content=content)
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)
        return msg

    def list_messages(self, conversation_id: int) -> List[Message]:
        stmt = select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at.asc())
        return list(self.db.scalars(stmt))

