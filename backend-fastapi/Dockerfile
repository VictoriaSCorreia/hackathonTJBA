# Trocando para a base Alpine, que é mais leve
FROM python:3.12-alpine

# Alpine usa 'apk' em vez de 'apt-get'
# 'build-base' é o equivalente a 'build-essential'
# Adicionamos também 'libffi-dev' que pode ser necessário para algumas libs
ENV POETRY_VERSION=1.8.3 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apk add --no-cache build-base curl libffi-dev

# O resto do processo é o mesmo
RUN curl -sSL https://install.python-poetry.org | python3 - && ln -s /root/.local/bin/poetry /usr/local/bin/poetry
WORKDIR /app
COPY pyproject.toml poetry.lock* /app/
RUN poetry install --no-root --no-interaction --no-ansi
COPY . /app/
EXPOSE 8000
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]