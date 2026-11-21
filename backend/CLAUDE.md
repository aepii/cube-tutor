# Backend

The schema comes only from Alembic: the backend container runs `alembic upgrade head` before uvicorn. Never call `create_all`. See [docs/backend.md § Migrations](../docs/backend.md#migrations).

```powershell
docker compose exec backend python -m seed.seed_algorithms   # seed a fresh DB
```

## Changing the schema

1. Edit the model in `app/models/`.
2. `docker compose exec backend alembic revision --autogenerate -m "<what>"`, then read the generated file in `alembic/versions/` and fix it by hand (autogenerate misses renames, server defaults, data moves). Give new constraints explicit names.
3. `docker compose exec backend alembic upgrade head`, then run pytest. `tests/test_migrations.py` fails if models and migrations disagree, or if `downgrade` breaks.

## Tests and lint

Run on the host with `backend/.venv` (that's what `/verify` uses). Tests need Compose Postgres up; they use their own `cubetutor_test` database. See [docs/backend.md § Tests](../docs/backend.md#tests).

```powershell
cd backend
.venv\Scripts\python -m pip install -r requirements-dev.txt   # once
.venv\Scripts\python -m pytest -q
.venv\Scripts\python -m ruff check .          # --fix for import order / pyupgrade
```

- Add dev-only tools to `requirements-dev.txt` (UTF-8), not `requirements.txt` (UTF-16 until 4c).
- Known bugs are pinned with `@pytest.mark.xfail(strict=True, reason="<sub-step>: …")`. A fix makes the test XPASS, which fails the run: remove the marker in the same PR.
