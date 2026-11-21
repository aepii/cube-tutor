# 0005 — One Python package and image for API + worker, managed by uv

**Status:** accepted (4c, issue #18). Amends [0004](0004-celery-redis-worker.md): Celery stays, but its code no longer lives in a bind-mounted `shared/` folder.

**Evidence:** ROADMAP §4.1 #6 (backend image broken without the bind mount), §4.2 (one package; UTF-16 `pip freeze` files), §3.11 (a migration job runs before each rollout).

## Context
- Before 4c there were two Python projects. `backend/` held FastAPI, and `worker/` was a one-line `main.py` importing `shared.celery_app`. The Celery app and its task lived in repo-root `shared/`, which was bind-mounted into both containers. `routes/images.py` imported `shared.tasks`, so the backend image only worked under Compose.
- Dependencies were two UTF-16 `pip freeze` dumps: 70+ transitive pins, unused packages (`numpy`, `sentry-sdk`, `beautifulsoup4`, `fastapi-cloud-cli`), and both `psycopg2` and `psycopg2-binary`. The worker image had no database or ORM packages, so tasks couldn't touch the models.
- The seed ran only by hand.

## Decision
- **One package:** the Celery app and tasks live in `backend/app/worker/`. The API, worker, migrations and seed share one dependency set.
- **One image** (`backend/Dockerfile`, multi-stage, non-root, no dev tools), **three commands:**

  | Service | Command |
  |---|---|
  | `migrate` (one-shot) | `alembic upgrade head && python -m seed.seed_algorithms` |
  | `backend` | `uvicorn app.main:app` (the image's default CMD; host, port and workers come from `UVICORN_*` env) |
  | `celery` | `celery -A app.worker.celery_app worker` |

  `backend` and `celery` start only after `migrate` exits 0. This mirrors the Container Apps migration job planned in §3.11.
- **uv:** `backend/pyproject.toml` lists direct dependencies only, with pytest/ruff/httpx in the `dev` group, and `uv.lock` pins the rest. The image runs `uv sync --frozen --no-dev`, and `/verify` runs `uv sync --locked`.

## Alternatives
- **Keep two images (API / worker) from one package.** Rejected: the dependency sets are nearly the same, and the scan worker will need the models. A second image doubles the build and push work for nothing.
- **pip + a hand-trimmed `requirements.txt` (+ pip-tools).** Workable. uv gives a cross-platform lockfile, dependency groups and much faster installs from one tool, and its Docker pattern (a dependency layer cached separately from the code) is well documented.
- **Poetry.** Slower, and its dependency format is its own rather than standard `[project]` metadata.
- **Migrate inside the API container's command (what 4b did).** With more than one replica, each would race to migrate. A separate one-shot job runs once per rollout and blocks the rollout if it fails.

## Consequences
- \+ The image runs anywhere with env vars only. No bind mounts, no `shared/` Python code.
- \+ Reproducible installs. `uv sync --locked` fails when `pyproject.toml` and `uv.lock` disagree.
- \+ A fresh database is migrated and seeded on `docker compose up`.
- − The worker image carries FastAPI/uvicorn it doesn't use (a few MB).
- − Contributors need `uv` on their machine (`winget install --id astral-sh.uv`).
- − Deliberate caps to hold today's behavior: `sqlalchemy<2.1` (2.1 defaults `postgresql://` to psycopg 3), `sqlmodel<0.0.32` (newer versions change the datetime column type, which would need a migration), `bcrypt<5` (breaks passlib). Lifting each one is its own change.
- The raw data stays in `shared/data/raw/` (the scraper writes it, the frontend tests read it). The image copies it to `/shared/data/raw`, so the seed's default `<repo root>/shared/data/raw` resolves in both places. `SEED_DATA_DIR` overrides it.
