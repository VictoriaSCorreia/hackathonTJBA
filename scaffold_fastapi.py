from __future__ import annotations
import sys
from pathlib import Path

# Pastas que serão criadas
TEMPLATE_DIRS = [
    "app/api/v1/routes",
    "app/api",
    "app/core",
    "app/db",
    "app/models",
    "app/schemas",
    "app/services",
    "app/tests",
    "alembic/versions",
]

# Arquivos que serão criados (conteúdo embutido)
FILES: dict[str, str] = {
    ".gitignore": """__pycache__/
*.pyc
.env
.logs/
logs/
.mypy_cache/
.ruff_cache/
.pytest_cache/
**/.DS_Store
""",

    ".env.example": """APP_ENV=dev
SECRET_KEY=change-me
ACCESS_TOKEN_EXPIRE_MINUTES=60
DATABASE_URL=postgresql+viczinha02://app:app@localhost:5432/app
""",

    "pyproject.toml": """[tool.poetry]
name = "backend-fastapi"
version = "0.1.1"
description = "Backend base em FastAPI"
authors = ["Samuel Carvalho <samuel@example.com>"]
readme = "README.md"
packages = [{ include = "app" }]

[tool.poetry.dependencies]
python = "^3.12"
fastapi = "^0.115.0"
uvicorn = {extras=["standard"], version="^0.30.0"}
sqlmodel = "^0.0.22"
sqlalchemy = "^2.0.35"
alembic = "^1.13.2"
psycopg = {extras=["binary"], version="^3.2.1"}
pydantic-settings = "^2.4.0"
python-jose = {extras=["cryptography"], version="^3.3.0"}
passlib = {extras=["bcrypt"], version="^1.7.4"}
loguru = "^0.7.2"
httpx = "^0.27.2"

[tool.poetry.group.dev.dependencies]
pytest = "^8.3.3"
pytest-asyncio = "^0.24.0"
ruff = "^0.6.9"
mypy = "^1.13.0"

[tool.ruff]
line-length = 100

[tool.mypy]
python_version = "3.12"
ignore_missing_imports = true
warn_unused_ignores = true
strict_optional = true

[build-system]
requires = ["poetry-core>=1.0.0"]
build-backend = "poetry.core.masonry.api"
""",

    "Dockerfile": """FROM python:3.12-slim
ENV POETRY_VERSION=1.8.3 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y build-essential curl && rm -rf /var/lib/apt/lists/*
RUN curl -sSL https://install.python-poetry.org | python3 - && ln -s /root/.local/bin/poetry /usr/local/bin/poetry
WORKDIR /app
COPY pyproject.toml poetry.lock* /app/
RUN poetry install --no-root --no-interaction --no-ansi
COPY . /app
EXPOSE 8000
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
""",

    "docker-compose.yml": """services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: app
      POSTGRES_USER: app
      POSTGRES_PASSWORD: app
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  api:
    build: .
    depends_on:
      - db
    environment:
      - DATABASE_URL=postgresql+viczinha02://app:app@db:5432/app
      - APP_ENV=dev
    ports:
      - "8000:8000"
    command: poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

volumes:
  pgdata:
""",

    "Makefile": """.PHONY: up down bash fmt lint test migrate revision
up:
\tdocker compose up -d --build
down:
\tdocker compose down -v
bash:
\tdocker compose exec api bash
fmt:
\tdocker compose exec api poetry run ruff check --fix .
lint:
\tdocker compose exec api poetry run ruff check . && \\
\tdocker compose exec api poetry run mypy app
test:
\tdocker compose exec api poetry run pytest -q
migrate:
\tdocker compose exec api poetry run alembic upgrade head
revision:
\tdocker compose exec api poetry run alembic revision -m "auto" --autogenerate
""",

    "alembic.ini": """[alembic]
script_location = alembic
sqlalchemy.url = %(DATABASE_URL)s
""",

    "alembic/env.py": """from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from app.core.config import settings
from app.db.base import SQLModel
from app.models import user  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata

def _get_config_section():
    section = config.get_section(config.config_ini_section) or {}
    section["sqlalchemy.url"] = settings.DATABASE_URL
    return section

def run_migrations_offline() -> None:
    context.configure(url=settings.DATABASE_URL, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(_get_config_section(), prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
""",

    "app/main.py": """from fastapi import FastAPI
from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.users import router as users_router

app = FastAPI(title="Backend FastAPI Base", version="0.1.1")
app.include_router(health_router, prefix="/api/v1", tags=["health"])
app.include_router(users_router, prefix="/api/v1", tags=["users"])
""",

    "app/api/v1/routes/health.py": """from fastapi import APIRouter
router = APIRouter()
@router.get('/health', summary='Healthcheck')
async def healthcheck():
    return {'status': 'ok'}
""",

    "app/api/v1/routes/users.py": """from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserRead
from app.services.user_service import UserService
from app.api.deps import get_db

router = APIRouter(prefix='/users')

@router.post('/', response_model=UserRead, status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    service = UserService(db)
    return service.create_user(payload)

@router.get('/{user_id}', response_model=UserRead)
def get_user(user_id: int, db: Session = Depends(get_db)):
    service = UserService(db)
    user = service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    return user
""",

    "app/api/deps.py": """from collections.abc import Generator
from app.db.session import SessionLocal

def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
""",

    "app/core/logging.py": """from loguru import logger
logger.add('logs/app.log', rotation='10 MB', retention='7 days', enqueue=True)
""",

    "app/db/session.py": """from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
""",

    "app/db/base.py": """from sqlmodel import SQLModel
from app.models.user import User  # noqa: F401 - importa modelos para metadados
__all__ = ['SQLModel', 'User']
""",

    "app/models/user.py": """from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import UniqueConstraint

class User(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email", name="uq_users_email"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True)
    full_name: str
""",

    "app/schemas/user.py": """from pydantic import BaseModel, EmailStr, ConfigDict

class UserBase(BaseModel):
    email: EmailStr
    full_name: str

class UserCreate(UserBase):
    pass

class UserRead(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
""",

    "app/services/user_service.py": """from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate

class UserService:
    def __init__(self, db: Session):
        self.db = db

    def create_user(self, payload: UserCreate) -> User:
        user = User(email=payload.email, full_name=payload.full_name)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_user(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)
""",

    "app/tests/conftest.py": """import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture()
def client():
    return TestClient(app)
""",

    "app/tests/test_health.py": """def test_health(client):
    r = client.get('/api/v1/health')
    assert r.status_code == 200
    assert r.json() == {'status': 'ok'}
""",

    "README.md": '''# Backend FastAPI Base

## Rodando com Docker
```bash
make up
# http://localhost:8000/docs
'''}

def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(content, encoding="utf-8")
        print(f"[create] {path}")
    else:
        print(f"[skip] {path} (já existe)")

def main() -> None:
    project = sys.argv[1] if len(sys.argv) > 1 else "backend-fastapi"
    root = Path(project)
    root.mkdir(parents=True, exist_ok=True)
    print(f"-> Criando estrutura em: {root.resolve()}")

    # Pastas
    for d in TEMPLATE_DIRS:
        (root / d).mkdir(parents=True, exist_ok=True)
        print(f"[mkdir]  {root/d}")

    # Arquivos
    for rel, content in FILES.items():
        write_file(root / rel, content)

    print(
        "\nPronto!\n→ Próximos passos:\n"
        f"  1) cd {project}\n"
        "  2) cp .env.example .env\n"
        "  3) docker compose up -d --build\n"
        "  4) Abrir http://localhost:8000/docs\n"
        "  5) poetry run alembic revision -m 'init' --autogenerate && poetry run alembic upgrade head\n"
    )

if __name__ == "__main__":
    main()