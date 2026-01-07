.PHONY: help run-backend run-frontend lint format test \
	backend-venv backend-install backend-lint backend-format backend-test \
	frontend-install frontend-lint frontend-format

BACKEND_DIR := backend
FRONTEND_DIR := frontend

PY := python3
BACKEND_VENV := .venv
BACKEND_BIN := $(BACKEND_VENV)/bin
UV_CACHE_DIR := .uv-cache

help:
	@echo "Targets:"
	@echo "  run-backend     Run FastAPI backend (auto-sets up venv + deps)"
	@echo "  run-frontend    Run Next.js frontend (auto-installs deps)"
	@echo "  lint            Lint backend + frontend"
	@echo "  format          Auto-format backend + frontend"
	@echo "  test            Run backend tests (pytest)"

backend-venv:
	@cd $(BACKEND_DIR) && [ -d .venv ] || $(PY) -m venv .venv

backend-install: backend-venv
	@cd $(BACKEND_DIR) && $(BACKEND_BIN)/pip install -q --upgrade pip uv
	@cd $(BACKEND_DIR) && UV_CACHE_DIR=$(UV_CACHE_DIR) $(BACKEND_BIN)/uv pip install --python $(BACKEND_BIN)/python -r requirements.txt -r requirements-dev.txt

backend-format: backend-install
	@cd $(BACKEND_DIR) && $(BACKEND_BIN)/ruff format .

backend-lint: backend-install
	@cd $(BACKEND_DIR) && $(BACKEND_BIN)/ruff check .

backend-test: backend-install
	@cd $(BACKEND_DIR) && $(BACKEND_BIN)/pytest

run-backend: backend-install
	@cd $(BACKEND_DIR) && $(BACKEND_BIN)/alembic upgrade head
	@cd $(BACKEND_DIR) && $(BACKEND_BIN)/uvicorn main:app --reload

frontend-install:
	@cd $(FRONTEND_DIR) && ( [ -f package-lock.json ] && npm ci --cache .npm-cache || npm install --cache .npm-cache )

frontend-format: frontend-install
	@cd $(FRONTEND_DIR) && npm run format

frontend-lint: frontend-install
	@cd $(FRONTEND_DIR) && npm run lint

run-frontend: frontend-install
	@cd $(FRONTEND_DIR) && npm run dev

format: backend-format frontend-format

lint: backend-lint frontend-lint

test: backend-test
