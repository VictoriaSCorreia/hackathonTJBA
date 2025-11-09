from __future__ import annotations

from typing import Tuple, Optional
from functools import lru_cache
import io

import soundfile as sf
from app.core.config import settings

# Importe o KittenTTS. Isso falhará se não for instalado via Dockerfile/pyproject
try:
    from kittentts import KittenTTS
except ImportError:
    print("KittenTTS não instalado. O serviço de TTS não funcionará.")
    KittenTTS = None  # type: ignore


class TTSServiceError(RuntimeError):
    pass


@lru_cache(maxsize=1)
def get_tts_model() -> KittenTTS:
    """
    Carrega o modelo KittenTTS e o mantém em cache (LRU cache de tamanho 1).
    Isso evita recarregar o modelo do disco a cada requisição.
    """
    if not KittenTTS:
        raise TTSServiceError("Biblioteca KittenTTS não está instalada.")
    
    try:
        model_id = settings.KITTEN_TTS_MODEL
        if not model_id:
            raise TTSServiceError("KITTEN_TTS_MODEL não está configurado.")
        
        # Carrega o modelo (pode levar alguns segundos na primeira vez)
        model = KittenTTS(model_id)
        return model
    except Exception as e:
        raise TTSServiceError(f"Falha ao carregar o modelo KittenTTS '{model_id}': {e}")


def generate_speech_sync(
    text: str,
    *,
    voice_id: Optional[str] = None,
) -> Tuple[bytes, str]:
    """
    Gera áudio (WAV) de forma síncrona usando KittenTTS.
    
    Retorna:
        Tuple[bytes, str]: (audio_bytes, media_type)
    """
    if not text or not text.strip():
        raise TTSServiceError("Texto para síntese não pode ser vazio")

    model = get_tts_model()
    
    selected_voice = voice_id or settings.KITTEN_TTS_VOICE_ID
    sample_rate = settings.KITTEN_TTS_SAMPLE_RATE

    try:
        # Gera o array numpy de áudio
        audio_array = model.generate(text, voice=selected_voice)
        
        if audio_array is None:
            raise TTSServiceError("Modelo não retornou dados de áudio.")

        # Converte o array numpy para bytes WAV em memória
        buffer = io.BytesIO()
        sf.write(
            buffer,
            audio_array,
            samplerate=sample_rate,
            format='WAV',
            subtype='PCM_16'
        )
        buffer.seek(0)
        audio_bytes = buffer.read()
        
        return audio_bytes, "audio/wav"

    except Exception as e:
        # Captura erros do 'model.generate()' ou 'sf.write()'
        raise TTSServiceError(f"Falha na geração do áudio: {e}")