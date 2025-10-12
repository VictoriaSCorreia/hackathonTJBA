.PHONY: up down bash fmt lint test migrate revision
up:
	docker compose up -d --build
down:
	docker compose down -v
bash:
	docker compose exec api bash
fmt:
	docker compose exec api poetry run ruff check --fix .
lint:
	docker compose exec api poetry run ruff check . && \
	docker compose exec api poetry run mypy app
test:
	docker compose exec api poetry run pytest -q
migrate:
	docker compose exec api poetry run alembic upgrade head
revision:
	docker compose exec api poetry run alembic revision -m "auto" --autogenerate
