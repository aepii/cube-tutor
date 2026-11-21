---
name: verify
description: Run CubeTutor's full pre-handoff check (frontend tsc, jest, expo lint, web + android exports, plus backend/worker ruff and pytest when configured). Use before handing work back to the user or before drafting a PR.
---

# Verify

Run the bundled script from the repo root with the Bash tool (Git Bash). Exports are slow, so use the maximum timeout:

```bash
bash .claude/skills/verify/verify.sh      # Bash tool timeout: 600000
```

What it does, in order, stopping at the first failure:

1. `frontend/`: `npx tsc --noEmit`
2. `frontend/`: `npx jest`
3. `frontend/`: `npx expo lint` (0 errors required; warnings pass)
4. `frontend/`: `npx expo export --platform web` into a temp dir
5. `frontend/`: `npx expo export --platform android` into a temp dir
6. `backend/` and `worker/`: `ruff check .` and `pytest -q`, **only if configured** (`ruff.toml`, `.ruff.toml`, `[tool.ruff]`; `pytest.ini`, `conftest.py`, `[tool.pytest…]`, `[tool:pytest]`, `[pytest]`). These run with the service's own `.venv` Python. If a tool is configured but there is no `.venv`, that step fails. Otherwise unconfigured tools show as SKIP.

The temp dir (exports and logs) is deleted on exit, pass or fail.

## Reporting

- Give the user the PASS/FAIL/SKIP line for each step, as printed.
- On failure: show the failing step's output (the script prints the last 80 lines), say what's wrong, and don't run later steps by hand. Fix the problem if it's in the current change, then rerun the whole script.
- Don't call the work done or verified unless the script ends with `All checks passed.`
