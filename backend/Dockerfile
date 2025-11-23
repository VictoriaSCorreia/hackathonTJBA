FROM python:3.12-slim

ENV POETRY_VERSION=1.8.3 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# System dependencies required by audio/ML stack
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ca-certificates \
    libffi-dev \
    ffmpeg \
    flac \
    libpq-dev \
    libsndfile1 \
    libsndfile1-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - \
    && ln -s /root/.local/bin/poetry /usr/local/bin/poetry

WORKDIR /app
COPY pyproject.toml poetry.lock* /app/

# Install Python deps
RUN poetry install --no-root --no-interaction --no-ansi

# Copy project
COPY . /app/

# Preload KittenTTS model during build (non-fatal if offline)
RUN poetry run python - <<'PY' || true
from app.core.config import settings
try:
    from kittentts import KittenTTS
    print(f"[build] Preloading KittenTTS model: {settings.KITTEN_TTS_MODEL}")
    KittenTTS(settings.KITTEN_TTS_MODEL)
    print("[build] KittenTTS model cached.")
except Exception as e:
    print(f"[build] KittenTTS preload skipped/failed: {e}")
PY

EXPOSE 8000
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

