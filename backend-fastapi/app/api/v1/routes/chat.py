from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.schemas.agent import ChatRequest, ChatResponse
from app.services.legal_agent import (
    generate_clarify_questions,
    generate_final_answer,
    parse_q123,
    is_new_topic,
)


router = APIRouter()

# Estado mínimo em memória para dois passos do endpoint stateless
# Chaveado por conversation_id.
CHAT_STATE: Dict[str, Dict[str, Any]] = {}


@router.post("/chat", response_model=ChatResponse, summary="Chat do agente jurídico")
def chat(req: ChatRequest) -> ChatResponse:
    if not settings.COHERE_API_KEY:
        raise HTTPException(status_code=500, detail="COHERE_API_KEY não configurada no ambiente")

    conv_id = req.conversation_id or "local-thread"

    rec = CHAT_STATE.get(conv_id)
    if rec and rec.get("phase") == "clarify_sent":
        # Etapa B: usuário respondeu U1
        U0 = rec.get("U0") or ""
        clarify_block = rec.get("clarify") or ""
        Qs = parse_q123(clarify_block)
        U1 = req.user_message

        try:
            if is_new_topic(U0, Qs, U1):
                # Recomeça Etapa A
                clar = generate_clarify_questions(user_message=U1, k=5)
                CHAT_STATE[conv_id] = {"phase": "clarify_sent", "U0": U1, "clarify": clar}
                return ChatResponse(response_text=clar, citations=[], conversation_id=conv_id)

            final = generate_final_answer(U0=U0, Qs=Qs, U1=U1, conversation_id=conv_id, k=5)
            # Limpa estado após resposta final
            CHAT_STATE.pop(conv_id, None)
            return ChatResponse(
                response_text=final.get("text", ""),
                citations=final.get("citations") or [],
                conversation_id=conv_id,
            )
        except Exception as e:
            # Em caso de falha, reseta estado e repassa erro
            CHAT_STATE.pop(conv_id, None)
            raise HTTPException(status_code=500, detail=f"Erro ao gerar resposta final: {e}")
    else:
        # Etapa A: primeira passada
        try:
            clar = generate_clarify_questions(user_message=req.user_message, k=5)
            CHAT_STATE[conv_id] = {"phase": "clarify_sent", "U0": req.user_message, "clarify": clar}
            return ChatResponse(response_text=clar, citations=[], conversation_id=conv_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao gerar perguntas de esclarecimento: {e}")

