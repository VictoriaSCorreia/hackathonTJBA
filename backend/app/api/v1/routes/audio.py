from __future__ import annotations

import os
import tempfile
from typing import Any, Dict

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.speech_to_text import transcribe_audio_file


router = APIRouter()

MAX_SECONDS = 30.0


@router.post("/speech-to-text", summary="Transcreve áudio (até 30s) em texto")
async def speech_to_text(audio: UploadFile = File(...)) -> Dict[str, Any]:
    if not audio:
        raise HTTPException(status_code=400, detail="Arquivo de áudio é obrigatório")

    # Persist upload to a temporary file
    suffix = os.path.splitext(audio.filename or "")[1] or ".bin"
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await audio.read())
            tmp_path = tmp.name
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha ao salvar áudio: {e}")

    try:
        transcript, duration = transcribe_audio_file(tmp_path, language="pt-BR")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass

    # Enforce 30s limit (best-effort; frontend should also limit)
    if duration and duration > (MAX_SECONDS + 1.0):
        raise HTTPException(status_code=400, detail=f"Áudio excede {MAX_SECONDS:.0f}s (duração ~{duration:.1f}s)")

    return {
        "transcript": transcript,
        "duration": duration,
    }

