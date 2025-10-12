from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import wave
from typing import Tuple

import speech_recognition as sr


def _run_ffmpeg_convert_to_wav(src_path: str, dst_path: str) -> None:
    """Convert any audio file to mono 16kHz WAV using ffmpeg.

    Requires `ffmpeg` to be available in the environment.
    """
    # -y overwrite, -ac 1 mono, -ar 16000 sample rate
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        src_path,
        "-ac",
        "1",
        "-ar",
        "16000",
        dst_path,
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _guess_ext(filename: str) -> str:
    base, ext = os.path.splitext(filename or "")
    return (ext or "").lower()


def _get_wav_duration_seconds(path: str) -> float:
    with wave.open(path, "rb") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate() or 1
        return frames / float(rate)


def transcribe_audio_file(filepath: str, *, language: str = "pt-BR") -> Tuple[str, float]:
    """Transcribe an audio file to text using Google Web Speech API via SpeechRecognition.

    - Converts input to 16kHz mono WAV with ffmpeg when needed.
    - Returns (transcript, duration_seconds).
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(filepath)

    # Prepare temp workspace
    workdir = tempfile.mkdtemp(prefix="stt_")
    src_copy = os.path.join(workdir, os.path.basename(filepath))
    shutil.copyfile(filepath, src_copy)

    # Always convert to WAV (mono/16k) for consistent recognition
    wav_path = os.path.join(workdir, "audio.wav")
    try:
        _run_ffmpeg_convert_to_wav(src_copy, wav_path)
    except Exception as e:
        # Cleanup and rethrow for API layer
        shutil.rmtree(workdir, ignore_errors=True)
        raise RuntimeError(f"Falha ao converter áudio para WAV: {e}")

    # Compute duration (server-side check if useful)
    try:
        duration = _get_wav_duration_seconds(wav_path)
    except Exception:
        duration = 0.0

    recognizer = sr.Recognizer()
    transcript = ""
    try:
        with sr.AudioFile(wav_path) as source:
            audio = recognizer.record(source)
        try:
            transcript = recognizer.recognize_google(audio, language=language)
        except sr.UnknownValueError:
            transcript = "[Inaudível]"
        except sr.RequestError:
            transcript = "[Erro de transcrição]"
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    return transcript, float(duration)

