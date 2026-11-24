#!/usr/bin/env bash
# Pre-handoff checks for CubeTutor. Prints PASS/FAIL/SKIP per step and stops at
# the first failure, printing that step's output. Exit code 0 = all passed.
set -u

ROOT="$(git rev-parse --show-toplevel)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
LOG="$TMP/step.log"

# Native Windows tools (node, expo) need a Windows path for the export dir.
win_path() { if command -v cygpath >/dev/null 2>&1; then cygpath -w "$1"; else echo "$1"; fi; }

n=0
step() { # step <name> <dir> <cmd...>
  local name="$1" dir="$2"; shift 2
  n=$((n + 1))
  printf '[%d] %-32s ' "$n" "$name"
  local start=$SECONDS
  if (cd "$dir" && "$@") >"$LOG" 2>&1; then
    echo "PASS ($((SECONDS - start))s)"
  else
    echo "FAIL ($((SECONDS - start))s)"
    echo "---- last 80 lines of: $* (in ${dir#"$ROOT"/}) ----"
    tail -n 80 "$LOG"
    exit 1
  fi
}
skip() { n=$((n + 1)); printf '[%d] %-32s SKIP (%s)\n' "$n" "$1" "$2"; }
fail() { n=$((n + 1)); printf '[%d] %-32s FAIL\n%s\n' "$n" "$1" "$2"; exit 1; }

# ---- Frontend ----
FE="$ROOT/frontend"
step "frontend: tsc --noEmit"     "$FE" npx tsc --noEmit
step "frontend: jest"             "$FE" npx jest
step "frontend: expo lint"        "$FE" npx expo lint   # nonzero exit on any error; warnings pass
step "frontend: export web"       "$FE" npx expo export --platform web --output-dir "$(win_path "$TMP/web")"
step "frontend: export android"   "$FE" npx expo export --platform android --output-dir "$(win_path "$TMP/android")"

# ---- Backend (one uv project: API, worker, migrations, seed) ----
BE="$ROOT/backend"
if [ -f "$BE/pyproject.toml" ]; then
  if ! command -v uv >/dev/null 2>&1; then
    fail "backend: uv sync --locked" "uv is not installed (winget install --id astral-sh.uv)."
  fi
  # --locked fails if uv.lock is out of date with pyproject.toml.
  step "backend: uv sync --locked"   "$BE" uv sync --locked
  step "backend: ruff check"         "$BE" uv run --frozen ruff check .
  step "backend: ruff format --check" "$BE" uv run --frozen ruff format --check .
  step "backend: pytest"             "$BE" uv run --frozen pytest -q
fi

echo "All checks passed."
