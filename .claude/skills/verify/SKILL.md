---
name: verify
description: Run CubeTutor's full pre-handoff check (frontend tsc, jest, expo lint, web + android exports, plus backend uv sync, ruff and pytest). Use before handing work back to the user or before drafting a PR.
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
6. `backend/` (one uv project, ADR 0005): `uv sync --locked` (fails if `uv.lock` is stale), then `uv run --frozen ruff check .` and `uv run --frozen pytest -q`. Needs `uv` on PATH and Compose Postgres up (tests use the `cubetutor_test` database). Missing `uv` is a FAIL.

The temp dir (exports and logs) is deleted on exit, pass or fail.

## Reporting

- Give the user the PASS/FAIL/SKIP line for each step, as printed.
- On failure: show the failing step's output (the script prints the last 80 lines), say what's wrong, and don't run later steps by hand. Fix the problem if it's in the current change, then rerun the whole script.
- Don't call the work done or verified unless the script ends with `All checks passed.`
