# Backend

One uv project for the API (`app/`), the Celery worker (`app/worker/`), migrations and the seed; one image ([`Dockerfile`](Dockerfile), build context = repo root), three Compose commands ([ADR 0005](../docs/decisions/0005-one-python-package-uv.md)).

The schema comes only from Alembic. The one-shot `migrate` service runs `alembic upgrade head && python -m seed.seed_algorithms` before `backend` and `celery` start. Never call `create_all`. See [docs/backend.md § Migrations](../docs/backend.md#migrations).

```powershell
docker compose run --rm migrate                 # re-run migrations + the (idempotent) seed
docker compose logs migrate                     # why backend/celery didn't start
docker compose up -d --build                    # after changing dependencies or worker code (only backend has a live mount)
```

## Changing the schema

1. Edit the model in `app/models/`.
2. `docker compose exec backend alembic revision --autogenerate -m "<what>"`, then read the generated file in `alembic/versions/` and fix it by hand (autogenerate misses renames, server defaults, data moves). Give new constraints explicit names.
3. `docker compose exec backend alembic upgrade head`, then run pytest. `tests/test_migrations.py` fails if models and migrations disagree, or if `downgrade` breaks.

## Tests and lint

Run on the host with uv (that's what `/verify` uses; install: `winget install --id astral-sh.uv`). Tests need Compose Postgres up; they use their own `cubetutor_test` database. See [docs/backend.md § Tests](../docs/backend.md#tests).

```powershell
cd backend
uv sync                      # once, and after pulling dependency changes
uv run pytest -q
uv run ruff check .          # --fix for import order / pyupgrade
```

- Dependencies: `uv add <pkg>` (runtime) or `uv add --dev <pkg>` (tests/lint). Commit `uv.lock`. The image installs `--no-dev`, so anything the app imports must be a runtime dependency.
- Known bugs are pinned with `@pytest.mark.xfail(strict=True, reason="<sub-step>: …")`. A fix makes the test XPASS, which fails the run: remove the marker in the same PR.
