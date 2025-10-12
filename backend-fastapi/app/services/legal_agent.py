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
from app.services.final_prompt import build_final_prompt_v2
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
                    # Suporte a JSON estruturado de leis (know_base)
                    if isinstance(item, dict) and item.get("metadados"):
                        md = item.get("metadados", {})
                        numero = str(md.get("numero") or "").strip()
                        ano = str(md.get("ano") or "").strip()
                        tipo = (md.get("tipo_ato") or "Lei").strip()
                        ementa = (md.get("ementa") or "").strip()
                        fonte = (md.get("fonte") or {}).get("fonte_oficial_url") if md.get("fonte") else None
                        versao = md.get("versao") or {}
                        updated_at = versao.get("ultima_atualizacao") or md.get("data_epigrafe")

                        conteudo_plano = (item.get("conteudo_plano") or "").strip()
                        rag_chunks = item.get("rag_chunks") or []
                        rag_text = " ".join([str(c.get("text", "")).strip() for c in rag_chunks if c])
                        content = " \n ".join([c for c in [ementa, conteudo_plano, rag_text] if c])

                        title = (
                            f"{tipo} {numero}/{ano}".strip()
                            if (numero and ano)
                            else (md.get("titulo_oficial_raw") or os.path.basename(path))
                        )
                        tags = [
                            tipo.lower(),
                            numero,
                            ano,
                            f"{tipo} {numero}".strip(),
                        ]
                        if numero in {"7716", "12288", "14532"}:
                            tags.append("base_principal")

                        doc = {
                            "title": title,
                            "content": content,
                            "url": fonte,
                            "jurisdiction": "BR",
                            "updated_at": updated_at,
                            "tags": [t for t in tags if t],
                        }
                        doc["_fulltext"] = _normalize_text(
                            f"{doc['title']} {ementa} {conteudo_plano} {rag_text} {' '.join(doc['tags'])} BR"
                        )
                        docs.append(doc)
                        continue

                    # Formato genérico
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
                            "_fulltext": _normalize_text(f"{title} {content} {' '.join(tags)} {jurisdiction}"),
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
    # Resolve diretório da KB com fallback robusto
    candidates: List[str] = []
    if settings.KB_DIR:
        candidates.append(settings.KB_DIR)
    # Baseadas na estrutura do projeto
    here = os.path.abspath(os.path.dirname(__file__))
    project_root = os.path.abspath(os.path.join(here, "..", ".."))  # backend-fastapi
    candidates.extend(
        [
            os.path.join(project_root, "know_base"),
            os.path.join(project_root, "kb"),
            os.path.abspath(os.path.join(os.getcwd(), "know_base")),
            os.path.abspath(os.path.join(os.getcwd(), "kb")),
        ]
    )
    kb_dir = next((p for p in candidates if p and os.path.isdir(p)), settings.KB_DIR or "./kb")
    docs = load_kb_from_dir(kb_dir)
    if not docs:
        return KB_FALLBACK
    return docs


# --------------------------- RAG (keyword scoring) ---------------------------
def _tokenize(query: str) -> List[str]:
    # Usa classes Unicode para cobrir acentos/cedilha adequadamente
    return [t for t in re.split(r"[^\w]+", query.lower(), flags=re.UNICODE) if t]


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
    top = [
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

    # Inclui sempre as três fontes principais, se presentes
    def _is_priority(doc: Dict[str, Any]) -> bool:
        t = (doc.get("title") or "").lower()
        tags = [str(x).lower() for x in doc.get("tags", [])]
        keys = ["7716", "12288", "14532"]
        return any(k in t for k in keys) or any(any(k in tg for k in keys) for tg in tags)

    priority = [
        {
            "title": d["title"],
            "snippet": d.get("content", "")[:1000],
            "url": d.get("url"),
            "jurisdiction": d.get("jurisdiction"),
            "last_updated": d.get("updated_at"),
            "tags": d.get("tags", []),
        }
        for d in kb_docs
        if _is_priority(d)
    ]
    seen = set()
    merged: List[Dict[str, Any]] = []
    for d in priority + top:
        key = (d.get("title"), d.get("url"))
        if key in seen:
            continue
        seen.add(key)
        merged.append(d)
    # Retorna pelo menos as prioridades, com top k complementando
    return merged[: max(k, len(priority))]


# --------------------------- Prompt do sistema (NORMALIZADO) ---------------------------
GLOBAL_PROMPT = dedent(
    """ 
    [ROLE]
    Você é um Conselheiro Jurídico virtual. Entenda a situação do usuário, analise de forma neutra e didática,
    e aponte apenas as leis mais relacionadas. Não substitui um advogado.

    [FONTES PRIORITÁRIAS]
    Priorize as seguintes bases, escolhendo no máximo 2 por resposta:
      • Lei 7.716/1989 (Lei do Crime Racial).
      • Lei 14.532/2023 (altera a 7.716/1989 e o CP; injúria racial como racismo).
      • Lei 12.288/2010 (Estatuto da Igualdade Racial) — use somente se agregar ao entendimento do caso.
    Não listar outras normas correlatas.

    [TOM E ESTILO]
      • Linguagem formal, acessível e concisa.
      • SEMPRE linguagem condicional (“pode”, “em tese”, “há indícios de…”).
      • Empatia profissional, sem julgamentos ou certezas.

    [POLÍTICA DE RESPOSTA – DUAS FASES]
      Fase A (Esclarecimento)
        • Produza EXATAMENTE 3 perguntas objetivas para completar contexto.
        • A saída DEVE iniciar com <clarify> e terminar com </clarify>.
        • NÃO fazer análise jurídica nesta fase. Máx. 120 caracteres por pergunta.

      Fase B (Análise Final)
        • Estruture a resposta com seções curtas e objetivas.
        • Liste apenas 1–2 leis dentre as três prioritárias, explicando por que PODEM se aplicar.
        • Citar dispositivos apenas quando essencial (ex.: “Lei 7.716/1989, art. 20, §2º”).
        • Limites: não emitir conclusões definitivas; não orientar litígio/denúncia; foque em entendimento do problema.
        • Feche com “veredito provisório” (condicional) + caminhos de organização/compreensão + aviso de IA.

    [ESTRUTURA OBRIGATÓRIA DA FASE B]
      1) Entendimento do caso (2–3 linhas).
      2) Enquadramento jurídico possível (1 parágrafo, condicional).
      3) Leis potencialmente aplicáveis (apenas 1–2 dentre 7.716/1989; 14.532/2023; 12.288/2010, se agregar).
      4) Lacunas que podem mudar o enquadramento (bullets).
      5) Veredito provisório (condicional) com 2–4 opções de organização/compreensão (sem prescrever medidas legais).
      6) Aviso legal.

    [RESTRIÇÕES]
      • Proibido: opiniões políticas, julgamentos morais, prescrição de medidas legais, prometer resultado, modelos de petição.
      • Obrigatório: foco jurídico didático, clareza, e linguagem condicional.

    [SAÍDA/IDIOMA]
      • Responder em PT-BR, de forma clara e objetiva.
      • Usar “documents” apenas para embasar; não listar leis além das prioritárias.
    """
).strip()


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
        "preamble": GLOBAL_PROMPT,
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
    """Prompt para gerar exatamente 3 perguntas de esclarecimento (Fase A).
    O modelo receberá `documents` via call_model; aqui instruímos formato e regras.
    """
    prompt = dedent(
        f"""
        Você é um Conselheiro Jurídico. Nesta etapa, apenas esclareça o contexto.

        REGRAS:
        - Inicie a saída com <clarify> e termine com </clarify>.
        - Produza EXATAMENTE 3 perguntas (Q1, Q2, Q3), diretas e não sugestivas.
        - Foque em quem fez o quê, quando, onde e como; peça evidências (mensagens, e-mails, testemunhas, protocolos).
        - Não ofereça opinião jurídica aqui; não cite leis; até 120 caracteres por pergunta.

        Mensagem do usuário (U0):
        {user_message}

        FORMATO:
        <clarify>
        Q1: ...
        Q2: ...
        Q3: ...
        </clarify>
        """
    ).strip()
    return prompt


def _extract_questions_from_text(text: str) -> List[str]:
    """Extrai até 3 perguntas do texto retornado pelo modelo."""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    qmap: Dict[str, str] = {}
    for ln in lines:
        m = re.match(r"^Q([123])\s*:\s*(.+)$", ln, flags=re.IGNORECASE)
        if m:
            idx = m.group(1)
            qtext = _ensure_max_len(m.group(2), 120)
            if not qtext.endswith("?"):
                qtext += "?"
            qmap[idx] = qtext
    qs: List[Optional[str]] = [qmap.get("1"), qmap.get("2"), qmap.get("3")]
    if all(qs):
        return [q for q in qs if q]

    # fallback: coletar frases com '?'
    candidates: List[str] = []
    blob = " ".join(lines)
    for part in re.split(r"(?<=[\?])\s+", blob):
        part = part.strip()
        if not part:
            continue
        if part.endswith("?"):
            candidates.append(_ensure_max_len(part, 120))
        if len(candidates) >= 3:
            break
    # completar com perguntas padrão úteis
    default_qs = [
        "Qual é o seu objetivo específico com este pedido?",
        "Em qual jurisdição/estado isso se aplica?",
        "Há prazos, valores ou documentos relevantes que devemos considerar?",
    ]
    for dq in default_qs:
        if len(candidates) >= 3:
            break
        candidates.append(dq)
    return candidates[:3]


def enforce_three_questions(text: str) -> str:
    qs = _extract_questions_from_text(text)
    qs = (qs + [""] * 3)[:3]  # garante exatamente 3
    return "\n".join(
        [
            "<clarify>",
            f"Q1: {qs[0]}",
            f"Q2: {qs[1]}",
            f"Q3: {qs[2]}",
            "</clarify>",
        ]
    )


def parse_q123(clarify_block: str) -> List[str]:
    """Extrai Q1–Q3 de um bloco começando com <clarify>. Sempre retorna 3 strings."""
    return _extract_questions_from_text(clarify_block)


# build_final_prompt removido; usar build_final_prompt_v2
def combine_for_retrieval(U0: str, Qs: List[str], U1: str) -> str:
    parts = [U0] + Qs[:3] + [U1]
    return "\n".join([p for p in parts if p and p.strip()])


def is_new_topic(U0: str, Qs: List[str], U1: str) -> bool:
    """Heurística simples: baixa interseção de tokens entre (U0+Qs) e U1 sugere assunto novo."""
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


def generate_final_answer(
    U0: str, Qs: List[str], U1: str, conversation_id: Optional[str] = None, k: int = 5
) -> Dict[str, Any]:
    """Executa RAG com base em {U0, Qs, U1} e retorna resposta final + citações."""
    retrieval_query = combine_for_retrieval(U0, Qs, U1)
    documents = rag_retrieve(retrieval_query, k=k)
    prompt = build_final_prompt_v2(U0=U0, Qs=Qs, U1=U1)
    resp = call_model(user_message=prompt, conversation_id=conversation_id, documents=documents)
    return resp
