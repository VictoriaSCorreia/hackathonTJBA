from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ConversationCreate(BaseModel):
    title: Optional[str] = Field(default=None)


class ConversationRead(BaseModel):
    id: int
    guest_id: str
    title: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class MessageCreate(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str


class MessageRead(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ConversationWithMessages(BaseModel):
    conversation: ConversationRead
    messages: List[MessageRead]

