# Backend

Backend tables are created on startup by `create_all` (the Alembic history can't build a fresh DB yet; ROADMAP §4.1 #5).

```powershell
docker compose exec backend python -m seed.seed_algorithms   # seed a fresh DB
```
