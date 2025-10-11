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
from textwrap import dedent


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


# --------------------------- Two-step policy helpers ---------------------------
def _ensure_max_len(s: str, max_len: int = 240) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    return s[: max_len].rstrip()


def build_clarify_prompt(user_message: str) -> str:
    """Prompt para gerar exatamente 3 perguntas de esclarecimento.

    O modelo recebe os `documents` via parâmetro de `call_model`, então aqui apenas
    instruímos o comportamento e o formato de saída.
    """
    prompt = dedent(
        f"""
        Você é um assistente útil.
        Tarefa: Faça exatamente 3 perguntas de esclarecimento antes de responder.
        Regras:
        - Não responda ainda.
        - Perguntas objetivas, não redundantes, focadas no objetivo do usuário e no que foi recuperado do RAG.

        Mensagem do usuário (U0):
        {user_message}

        Formato de saída:
        <clarify>
        Q1: ...
        Q2: ...
        Q3: ...
        """
    ).strip()
    return prompt


def _extract_questions_from_text(text: str) -> list[str]:
    """Extrai até 3 perguntas do texto retornado pelo modelo.

    Preferência:
    - Linhas iniciando com Q1:/Q2:/Q3:
    - Caso não encontre, pega as 3 primeiras frases com '?'
    - Faz limpeza e truncamento
    """
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    qmap: dict[str, str] = {}
    for ln in lines:
        m = re.match(r"^Q([123])\s*:\s*(.+)$", ln, flags=re.IGNORECASE)
        if m:
            idx = m.group(1)
            qtext = _ensure_max_len(m.group(2))
            if qtext.endswith("?") is False:
                qtext += "?"
            qmap[idx] = qtext
    qs: list[str] = [qmap.get("1"), qmap.get("2"), qmap.get("3")]
    if all(qs):
        return [q for q in qs if q]

    # fallback: coletar frases com '?'
    candidates: list[str] = []
    blob = " ".join(lines)
    # quebrar em sentenças rudimentarmente
    for part in re.split(r"(?<=[\?])\s+", blob):
        part = part.strip()
        if not part:
            continue
        if part.endswith("?"):
            candidates.append(_ensure_max_len(part))
        if len(candidates) >= 3:
            break
    # se ainda insuficiente, crie perguntas genéricas úteis
    while len(candidates) < 3:
        default_qs = [
            "Qual é o seu objetivo específico com este pedido?",
            "Em qual jurisdição/estado isso se aplica?",
            "Há prazos, valores ou documentos relevantes que devamos considerar?",
        ]
        for dq in default_qs:
            if len(candidates) < 3:
                candidates.append(dq)
    return candidates[:3]


def enforce_three_questions(text: str) -> str:
    qs = _extract_questions_from_text(text)
    # garante exatamente 3
    qs = (qs + [""] * 3)[:3]
    return "\n".join(["<clarify>", f"Q1: {qs[0]}", f"Q2: {qs[1]}", f"Q3: {qs[2]}"])


def parse_q123(clarify_block: str) -> list[str]:
    """Extrai Q1–Q3 de um bloco começando com <clarify>. Sempre retorna 3 strings."""
    return _extract_questions_from_text(clarify_block)


def build_final_prompt(U0: str, Qs: list[str], U1: str) -> str:
    qs_fmt = "\n".join([f"Q{i+1}: {q}" for i, q in enumerate(Qs[:3])])
    prompt = dedent(
        f"""
        Você é um assistente útil.

        Contexto:
        - Objetivo original do usuário (U0):
        {U0}
        - Suas 3 perguntas:
        {qs_fmt}
        - Respostas do usuário (U1):
        {U1}

        Tarefa: Com base no RAG mais recente, produza a resposta final.
        Regras:
        - Seja direto, acionável e completo.
        - Não faça novas perguntas.
        """
    ).strip()
    return prompt


def combine_for_retrieval(U0: str, Qs: list[str], U1: str) -> str:
    parts = [U0] + Qs[:3] + [U1]
    return "\n".join([p for p in parts if p and p.strip()])


def is_new_topic(U0: str, Qs: list[str], U1: str) -> bool:
    """Heurística simples: se a sobreposição de tokens entre (U0+Qs) e U1 for muito baixa,
    consideramos que o usuário mudou de assunto.
    """
    base = f"{U0} \n {' '.join(Qs[:3])}"
    t_base = set(_tokenize(base))
    t_u1 = set(_tokenize(U1))
    if not t_base or not t_u1:
        return False
    inter = len(t_base & t_u1)
    ratio = inter / max(1, len(t_u1))
    return ratio < 0.15 and len(t_u1) >= 4


def generate_clarify_questions(user_message: str, k: int = 5) -> str:
    """Executa RAG sobre U0 e retorna um bloco <clarify> com Q1–Q3."""
    documents = rag_retrieve(user_message, k=k)
    prompt = build_clarify_prompt(user_message)
    resp = call_model(user_message=prompt, conversation_id=None, documents=documents)
    return enforce_three_questions(resp.get("text", ""))


def generate_final_answer(U0: str, Qs: list[str], U1: str, conversation_id: Optional[str] = None, k: int = 5) -> Dict[str, Any]:
    """Executa RAG com base em {U0, Qs, U1} e retorna resposta final + citações."""
    retrieval_query = combine_for_retrieval(U0, Qs, U1)
    documents = rag_retrieve(retrieval_query, k=k)
    prompt = build_final_prompt(U0=U0, Qs=Qs, U1=U1)
    resp = call_model(user_message=prompt, conversation_id=conversation_id, documents=documents)
    return resp
