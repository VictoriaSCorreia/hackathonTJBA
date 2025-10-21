from __future__ import annotations

import os
import io
import time
from pathlib import Path
from typing import Any, Dict, Optional
import mimetypes

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, Depends
from fastapi.responses import FileResponse

from app.api.deps import get_current_guest
from app.services.speech_to_text import transcribe_audio_file
from app.services.text_preprocessor import preprocess_transcript


router = APIRouter()

MAX_SECONDS = 30.0


def _get_upload_base() -> Path:
    # app/api/v1/routes -> parents[3] == app/
    base = Path(__file__).resolve().parents[3]
    uploads = base / "uploads" / "audio"
    uploads.mkdir(parents=True, exist_ok=True)
    return uploads


@router.post("/speech-to-text", summary="Transcreve áudio (até 30s) em texto")
async def speech_to_text(
    audio: UploadFile = File(...),
    conversation_id: Optional[int] = Form(default=None),
    current_user=Depends(get_current_guest),
) -> Dict[str, Any]:
    if not audio:
        raise HTTPException(status_code=400, detail="Arquivo de áudio é obrigatório")

    # Persist original upload for auditing/reference under uploads/audio/<guest>/<conv|misc>/
    try:
        guest_id = current_user.guest_id
    except Exception:
        # Should not happen due to Depends
        raise HTTPException(status_code=401, detail="Convidado inválido")

    uploads = _get_upload_base()
    subdir = uploads / guest_id / (str(conversation_id) if conversation_id else "misc")
    subdir.mkdir(parents=True, exist_ok=True)

    # Build filename based on timestamp, keep extension when possible
    orig_name = audio.filename or "recording.bin"
    ext = os.path.splitext(orig_name)[1] or ".bin"
    ts = time.strftime("%Y%m%d-%H%M%S")
    stored_name = f"{ts}{ext}"
    stored_path = subdir / stored_name

    # Save uploaded content to disk
    try:
        content = await audio.read()
        with open(stored_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha ao salvar áudio: {e}")

    # Transcribe from stored path (conversion handled inside service)
    try:
        transcript, duration = transcribe_audio_file(str(stored_path), language="pt-BR")
    except Exception as e:
        # Se a conversão falhar (ex.: codec não suportado), informe claramente
        detail = str(e)
        if 'ffmpeg' in detail.lower() or 'converter' in detail.lower():
            raise HTTPException(status_code=415, detail=f"Falha ao converter áudio (formato/codec não suportado?): {detail}")
        raise HTTPException(status_code=500, detail=detail)

    # Enforce 30s limit (best-effort; frontend should also limit)
    if duration and duration > (MAX_SECONDS + 1.0):
        # Keep the saved file, but reject the request
        raise HTTPException(status_code=400, detail=f"Áudio excede {MAX_SECONDS:.0f}s (duração ~{duration:.1f}s)")

    # Optional preprocessing (LLM ou regras simples), controlado por env STT_PREPROCESS_MODE
    cleaned, raw, mode = preprocess_transcript(transcript)

    return {
        "transcript": cleaned,
        "raw_transcript": raw,
        "transcript_preprocess_mode": mode,
        "duration": duration,
        "stored": True,
        "audio_filename": stored_name,
        "audio_dir": str(subdir.relative_to(_get_upload_base())),
        "audio_url": (f"/api/v1/audio/{conversation_id}/{stored_name}" if conversation_id else None),
        "audio_path": (f"audio/{conversation_id}/{stored_name}" if conversation_id else None),
    }


@router.get("/audio/{conversation_id}/{filename}", summary="Baixa arquivo de áudio da conversa")
def get_audio(
    conversation_id: int,
    filename: str,
    current_user=Depends(get_current_guest),
):
    # Básica proteção contra path traversal no nome do arquivo
    if "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Nome de arquivo inválido")

    base = _get_upload_base()
    target = base / current_user.guest_id / str(conversation_id) / filename
    try:
        resolved = target.resolve(strict=True)
        # Garante que o caminho está dentro da base
        resolved.relative_to(base)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    except Exception:
        raise HTTPException(status_code=403, detail="Acesso negado")

    media_type, _ = mimetypes.guess_type(str(resolved))
    return FileResponse(
        path=str(resolved),
        media_type=media_type or "application/octet-stream",
        filename=filename,
    )

