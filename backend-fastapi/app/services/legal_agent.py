# -*- coding: utf-8 -*-
"""
Serviço do agente jurídico: RAG local simples + Cohere Chat.

Características:
- Base de conhecimento em JSON (diretório configurável via settings.KB_DIR)
- Recuperação por palavras-chave com boosts por título e tags
- Geração de resposta via Cohere Command-R+ com documents
"""

from __future__ import annotations

import glob
import json
import os
import re
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, List, Optional

import cohere
from app.core.config import settings


# --------------------------- Helpers de texto/tempo ---------------------------
def _normalize_text(s: str) -> str:
    s = s.lower()
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _parse_date(s: Optional[str]) -> float:
    try:
        return datetime.fromisoformat(s).timestamp() if s else 0.0
    except Exception:
        return 0.0


# --------------------------- Carregamento da KB ---------------------------
def load_kb_from_dir(directory: str) -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []
    for path in glob.glob(os.path.join(directory, "**", "*.json"), recursive=True):
        try:
            with open(path, "r", encoding="utf-8") as f:
                payload = json.load(f)
                if isinstance(payload, dict):
                    payload = [payload]
                for item in payload:
                    title = item.get("title") or os.path.basename(path)
                    content = item.get("content") or item.get("snippet") or ""
                    url = item.get("url")
                    jurisdiction = item.get("jurisdiction") or "BR"
                    updated_at = item.get("updated_at") or item.get("last_updated")
                    tags = item.get("tags") or []
                    docs.append(
                        {
                            "title": str(title),
                            "content": str(content),
                            "url": url,
                            "jurisdiction": jurisdiction,
                            "updated_at": updated_at,
                            "tags": tags,
                            "_fulltext": _normalize_text(
                                f"{title} {content} {' '.join(tags)} {jurisdiction}"
                            ),
                        }
                    )
        except Exception:
            # Em produção, registrar erro de parsing
            pass
    return docs


# Fallback mínimo caso a pasta esteja vazia
KB_FALLBACK: List[Dict[str, Any]] = [
    {
        "title": "Como registrar boletim de ocorrência (BO) online",
        "content": (
            "A maioria dos estados possui delegacia eletrônica. Acesse o portal da sua Secretaria de "
            "Segurança, informe dados pessoais, descreva o fato e anexe documentos. Guarde o protocolo."
        ),
        "url": "https://exemplo.gov.br/delegacia-eletronica",
        "jurisdiction": "BR",
        "updated_at": "2025-06-01",
        "tags": ["criminal", "boletim", "ocorrência", "delegacia eletrônica"],
        "_fulltext": _normalize_text(
            "Como registrar boletim de ocorrência online A maioria dos estados possui delegacia eletrônica... BR criminal boletim ocorrência"
        ),
    },
    {
        "title": "Direitos do consumidor: produto com defeito",
        "content": (
            "O consumidor pode exigir troca, reparo ou devolução do valor. Prazos: 30 dias para vícios "
            "aparentes em produtos não duráveis e 90 dias em duráveis. Procure o Procon."
        ),
        "url": "https://exemplo.gov.br/direitos-consumidor",
        "jurisdiction": "BR",
        "updated_at": "2025-05-20",
        "tags": ["consumidor", "troca", "garantia", "procon"],
        "_fulltext": _normalize_text(
            "Direitos do consumidor produto com defeito troca reparo devolução prazo 30 90 dias Procon BR"
        ),
    },
]


@lru_cache(maxsize=1)
def get_kb_docs() -> List[Dict[str, Any]]:
    kb_dir = settings.KB_DIR or "./kb"
    docs = load_kb_from_dir(kb_dir)
    if not docs:
        return KB_FALLBACK
    return docs


# --------------------------- RAG (keyword scoring) ---------------------------
def _tokenize(query: str) -> List[str]:
    return [t for t in re.split(r"[^\wáéíóúâêîôûãõç]+", query.lower()) if t]


def simple_keyword_score(query: str, doc: Dict[str, Any]) -> float:
    tokens = set(_tokenize(query))
    if not tokens:
        return 0.0
    score = 0.0
    fulltext = doc.get("_fulltext", "")
    title = _normalize_text(doc.get("title", ""))
    tags = [_normalize_text(t) for t in doc.get("tags", [])]

    for tok in tokens:
        if tok in fulltext:
            score += 1.0
        if tok in title:
            score += 0.5
        if any(tok in tg for tg in tags):
            score += 0.25
    return score


def rag_retrieve(query: str, k: int = 5) -> List[Dict[str, Any]]:
    kb_docs = get_kb_docs()
    ranked = sorted(
        kb_docs,
        key=lambda d: (
            simple_keyword_score(query, d),
            _parse_date(d.get("updated_at")),
        ),
        reverse=True,
    )
    return [
        {
            "title": d["title"],
            "snippet": d.get("content", "")[:1000],
            "url": d.get("url"),
            "jurisdiction": d.get("jurisdiction"),
            "last_updated": d.get("updated_at"),
            "tags": d.get("tags", []),
        }
        for d in ranked[:k]
    ]


# --------------------------- Prompt do sistema ---------------------------
SYSTEM_PROMPT = (
    "Você é um agente jurídico que ajuda pessoas a entender \n"
    "opções e caminhos práticos para resolver problemas legais, SEM substituir\n"
    "a atuação de um(a) advogado(a).\n\n"
    "Instruções:\n"
    "- Responda sempre em PT-BR, com clareza e objetividade.\n"
    "- Use a base (documents) para embasar a resposta; referencie e liste as fontes relevantes.\n"
    "- Se faltarem detalhes importantes (jurisdição, prazos, valores, documentos), aponte quais informações o usuário deve reunir, mas ainda forneça orientações gerais.\n"
    "- Mostre passos práticos (checklists, onde ir, quais órgãos/links).\n"
    "- Seja cauteloso: não forneça interpretação jurídica definitiva; ressalte que é orientação informativa.\n"
    "- Quando houver conflito entre fontes, indique as alternativas e o que costuma variar por estado/município.\n"
    "- Estruture a saída: Resumo, Opções, Passo a passo, Documentos necessários, Prazos (se houver), Onde buscar ajuda, Fontes.\n"
)


# --------------------------- Cliente Cohere ---------------------------
@lru_cache(maxsize=1)
def get_cohere_client() -> cohere.Client:
    if not settings.COHERE_API_KEY:
        raise RuntimeError("COHERE_API_KEY não configurada")
    return cohere.Client(api_key=settings.COHERE_API_KEY)


def call_model(
    user_message: str,
    conversation_id: Optional[str],
    documents: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    # Adaptado para o SDK Cohere 5.x: usar 'message' e 'preamble' em vez de 'messages'
    kwargs: Dict[str, Any] = {
        "model": "command-r-plus-08-2024",
        "message": user_message,
        "preamble": SYSTEM_PROMPT,
    }
    if documents:
        # Sanitiza os documentos para o formato esperado pelo SDK Cohere 5.x
        def _sanitize_documents(docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            sanitized: List[Dict[str, Any]] = []
            for d in docs:
                nd: Dict[str, Any] = {}
                # Campos comuns suportados
                for key in ("title", "snippet", "url"):
                    if d.get(key) is not None:
                        nd[key] = str(d.get(key))
                # Campos adicionais convertidos para string
                if d.get("jurisdiction") is not None:
                    nd["jurisdiction"] = str(d.get("jurisdiction"))
                if d.get("last_updated") is not None:
                    nd["last_updated"] = str(d.get("last_updated"))
                if "tags" in d:
                    tags_val = d.get("tags")
                    if isinstance(tags_val, list):
                        nd["tags"] = ", ".join(map(str, tags_val))
                    else:
                        nd["tags"] = str(tags_val)
                sanitized.append(nd)
            return sanitized

        kwargs["documents"] = _sanitize_documents(documents)
    if conversation_id:
        kwargs["conversation_id"] = conversation_id

    co = get_cohere_client()
    resp = co.chat(**kwargs)

    # Extrai texto e citações de forma compatível com diferentes versões
    text = ""
    citations: List[Dict[str, Any]] = []
    try:
        if hasattr(resp, "text") and resp.text:
            text = resp.text
        elif getattr(resp, "message", None) and getattr(resp.message, "content", None):
            # Estrutura mais recente (message.content[0].text)
            parts = resp.message.content
            if parts and hasattr(parts[0], "text"):
                text = parts[0].text
    except Exception:
        text = str(resp)

    try:
        if getattr(resp, "citations", None):
            citations = resp.citations  # já é lista de dicts
    except Exception:
        citations = []

    return {
        "text": text,
        "citations": citations,
    }
