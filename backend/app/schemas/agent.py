from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    user_message: str = Field(..., description="Pergunta ou situação jurídica do usuário")
    conversation_id: Optional[str] = Field(
        None, description="ID da conversa (opcional, para thread local)"
    )


class ChatResponse(BaseModel):
    response_text: str
    citations: Optional[List[Dict[str, Any]]] = None
    conversation_id: Optional[str] = None

