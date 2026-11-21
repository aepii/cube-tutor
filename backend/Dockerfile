# syntax=docker/dockerfile:1
# One image for the API, the Celery worker and the migrate job (ADR 0005).
# Build context is the repo root, so the seed data in shared/data/raw is in reach:
#   docker build -f backend/Dockerfile -t cubetutor-backend .
# Commands:
#   (default)  uvicorn app.main:app      host/port/workers from UVICORN_* env
#   migrate    sh -c "alembic upgrade head && python -m seed.seed_algorithms"
#   worker     celery -A app.worker.celery_app worker --loglevel=info

ARG PYTHON_IMAGE=python:3.12-slim

# ---- builder: resolve the locked dependencies into /opt/venv ----
FROM ${PYTHON_IMAGE} AS builder
COPY --from=ghcr.io/astral-sh/uv:0.13.9 /uv /bin/uv

# The venv lives outside /app so the dev bind mount (./backend:/app) can't hide it.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock ./
# Dependencies only (no dev group: no pytest, ruff, httpx). This layer changes
# only when the lock does.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# ---- runtime: python + the venv + the code, no uv, no compilers ----
FROM ${PYTHON_IMAGE} AS runtime

RUN groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app

ENV PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UVICORN_HOST=0.0.0.0 \
    UVICORN_PORT=8000 \
    UVICORN_WORKERS=1

COPY --from=builder /opt/venv /opt/venv

# Code and data stay root-owned, so the app user can read but not modify them.
WORKDIR /app
COPY backend/alembic.ini ./
COPY backend/alembic ./alembic
COPY backend/app ./app
COPY backend/seed ./seed
# The seed's default data dir is <repo root>/shared/data/raw; here the "repo root" is /.
COPY shared/data/raw /shared/data/raw

USER app
EXPOSE 8000
CMD ["uvicorn", "app.main:app"]
