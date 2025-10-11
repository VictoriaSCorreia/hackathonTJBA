from fastapi import APIRouter, HTTPException

from app.schemas.agent import ChatRequest, ChatResponse
from app.services.legal_agent import call_model, rag_retrieve
from app.core.config import settings


router = APIRouter()


@router.post("/chat", response_model=ChatResponse, summary="Chat do agente jurídico")
def chat(req: ChatRequest) -> ChatResponse:
    if not settings.COHERE_API_KEY:
        raise HTTPException(status_code=500, detail="COHERE_API_KEY não configurada no ambiente")

    documents = rag_retrieve(req.user_message, k=5)
    result = call_model(
        user_message=req.user_message,
        conversation_id=req.conversation_id or "local-thread",
        documents=documents,
    )

    return ChatResponse(
        response_text=result.get("text", ""),
        citations=result.get("citations") or [],
        conversation_id=req.conversation_id or "local-thread",
    )

