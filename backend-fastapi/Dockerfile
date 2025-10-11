FROM python:3.12-slim


ENV PYTHONDONTWRITEBYTECODE=1  PYTHONUNBUFFERED=1  POETRY_VIRTUALENVS_CREATE=false

RUN python -m pip install --no-cache-dir --upgrade pip setuptools wheel && python -m pip install --no-cache-dir "poetry==1.8.3" && poetry --version

WORKDIR /app

COPY pyproject.toml poetry.lock* /app/

RUN poetry install --no-root --no-interaction --no-ansi

COPY . /app

EXPOSE 8000

CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
