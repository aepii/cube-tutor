# Backend

Backend tables are created on startup by `create_all` (the Alembic history can't build a fresh DB yet; ROADMAP §4.1 #5).

```powershell
docker compose exec backend python -m seed.seed_algorithms   # seed a fresh DB
```

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
