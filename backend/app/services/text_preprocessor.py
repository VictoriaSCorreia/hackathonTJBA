from __future__ import annotations

import re
from typing import Tuple

from app.core.config import settings

try:
    # Reutiliza o cliente Cohere já configurado pelo agente jurídico, se existir
    from app.services.legal_agent import get_cohere_client
except Exception:
    get_cohere_client = None  # type: ignore


_FILLERS = {
    "ah", "aham", "hã", "hum", "hmm", "é", "éé", "ééé",
    "tipo", "tipo assim", "né", "tá", "então", "aí", "daí",
    "sabe", "meio que", "ok", "certo", "bom",
}


def _basic_cleanup(text: str) -> str:
    s = text or ""
    # Normaliza espaços
    s = re.sub(r"\s+", " ", s).strip()

    # Remove muletas/fillers como palavras isoladas (limita falsos positivos)
    if s:
        # bordas de palavra e opcional pontuação ao redor
        for f in sorted(_FILLERS, key=len, reverse=True):
            pattern = rf"(?i)(?<!\w)\s*{re.escape(f)}\s*(?=[,.;:!?]|\b)"
            s = re.sub(pattern, " ", s)
        s = re.sub(r"\s+", " ", s).strip()

    # Conserta pontuação simples: remove duplicadas, garante ponto final
    s = re.sub(r"([.!?]){2,}", r"\1", s)
    s = re.sub(r"\s+([,.;:!?])", r"\1", s)
    if s and s[-1] not in ".!?":
        s = s + "."

    # Capitaliza início de frase básica
    try:
        s = s[:1].upper() + s[1:]
    except Exception:
        pass
    return s


def _llm_cleanup(text: str) -> str:
    if not get_cohere_client or not settings.COHERE_API_KEY:
        # Fallback para básico caso não haja LLM configurado
        return _basic_cleanup(text)

    co = get_cohere_client()
    # Prompt curto e focado em normalização; sem alterar o significado
    preamble = (
        "Você é um corretor de transcrições de fala para texto em PT-BR.\n"
        "Tarefas: 1) ajustar pontuação e caixa (sem formalizar demais),\n"
        "2) remover muletas de fala (ex.: 'ah', 'tipo', 'né', 'então'),\n"
        "3) corrigir pequenos erros de ditado preservando nomes, números e sentido,\n"
        "4) manter gírias necessárias e termos sensíveis,\n"
        "5) devolver apenas o texto limpo, em uma única linha.\n"
        "Proibido: inventar fatos, adicionar conteúdo, mudar datas/nomes, traduzir."
    )
    resp = co.chat(
        model="command-r-plus-08-2024",
        message=str(text or ""),
        preamble=preamble,
    )

    cleaned = ""
    try:
        if hasattr(resp, "text") and resp.text:
            cleaned = resp.text
        elif getattr(resp, "message", None) and getattr(resp.message, "content", None):
            parts = resp.message.content
            if parts and hasattr(parts[0], "text"):
                cleaned = parts[0].text
    except Exception:
        cleaned = str(resp)

    cleaned = (cleaned or "").strip()
    # Sanitização extra bem simples para evitar quebras
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned


def preprocess_transcript(text: str) -> Tuple[str, str, str]:
    """
    Aplica pré-processamento ao transcript de voz.
    Retorna (cleaned_text, raw_text, mode_usado).

    Controlado por settings.STT_PREPROCESS_MODE:
      - 'off': retorna o texto original sem alterações
      - 'basic': regras simples de limpeza
      - 'llm': usa o modelo LLM (Cohere) para normalização leve
    """
    raw = text or ""
    mode = (settings.STT_PREPROCESS_MODE or "off").strip().lower()
    if mode == "off":
        return raw, raw, "off"
    if mode == "llm":
        try:
            cleaned = _llm_cleanup(raw)
            if not cleaned:
                cleaned = _basic_cleanup(raw)
            return cleaned, raw, "llm"
        except Exception:
            # Fallback seguro
            return _basic_cleanup(raw), raw, "basic"
    # default: basic
    return _basic_cleanup(raw), raw, "basic"

