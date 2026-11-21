---
paths:
  - "backend/pyproject.toml"
  - "backend/uv.lock"
  - "scraper/requirements.txt"
---

- **Backend dependencies are managed by uv** (ADR 0005). Add with `uv add <pkg>` (runtime) or `uv add --dev <pkg>` (pytest, ruff, …), run from `backend/`. Never edit `uv.lock` by hand; commit it with `pyproject.toml`. List direct dependencies only.
- The image installs with `uv sync --frozen --no-dev`, so anything the app imports at runtime must be in `[project].dependencies`, not the dev group.
- Upper bounds in `pyproject.toml` (`bcrypt<5`, `sqlalchemy<2.1`, `sqlmodel<0.0.32`) are deliberate; the comment next to each says why. Lift one only in a PR that handles the breakage.
- `scraper/requirements.txt` is still UTF-16 (PowerShell `pip freeze >`); convert to UTF-8 if editing.
