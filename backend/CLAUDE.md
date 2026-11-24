# Backend

One uv project for the API (`app/`), migrations and the seed; one image ([`Dockerfile`](Dockerfile), build context = repo root), two Compose commands ([ADR 0005](../docs/decisions/0005-one-python-package-uv.md)).

The schema comes only from Alembic. The one-shot `migrate` service runs `alembic upgrade head && python -m seed.seed_algorithms` before `backend` starts. Never call `create_all`. See [docs/backend.md § Migrations](../docs/backend.md#migrations).

```powershell
docker compose run --rm migrate                 # re-run migrations + the (idempotent) seed
docker compose logs migrate                     # why backend didn't start
docker compose up -d --build                    # after changing dependencies or the Dockerfile
```

## Changing the schema

1. Edit the model in `app/models/`.
2. `docker compose exec backend alembic revision --autogenerate -m "<what>"`, then read the generated file in `alembic/versions/` and fix it by hand (autogenerate misses renames, server defaults, data moves). Give new constraints explicit names.
3. `docker compose exec backend alembic upgrade head`, then run pytest. `tests/test_migrations.py` fails if models and migrations disagree, or if `downgrade` breaks.

**Migrations must work with the code before them (expand → deploy → contract).** On Azure, the migration job runs on the new image while the old API revision keeps serving. Add tables, nullable or defaulted columns, and backfills first. Drop or rename what the old code reads only in a **later** deploy. Never rename or drop a column in the same PR as the code that stops using it. The seed runs on every deploy, so it must stay idempotent. See [docs/infra.md § The migration rule](../docs/infra.md#the-migration-rule-expand--deploy--contract).

## Tests and lint

Run on the host with uv (that's what `/verify` uses; install: `winget install --id astral-sh.uv`). Tests need Compose Postgres up; they use their own `cubetutor_test` database. See [docs/backend.md § Tests](../docs/backend.md#tests).

```powershell
cd backend
uv sync                      # once, and after pulling dependency changes
uv run pytest -q
uv run ruff check .          # --fix for import order / pyupgrade
uv run ruff format .         # CI and /verify run --check, so format before pushing
```

- Dependencies: `uv add <pkg>` (runtime) or `uv add --dev <pkg>` (tests/lint). Commit `uv.lock`. The image installs `--no-dev`, so anything the app imports must be a runtime dependency.
- Known bugs are pinned with `@pytest.mark.xfail(strict=True, reason="<sub-step>: …")`. A fix makes the test XPASS, which fails the run: remove the marker in the same PR.
