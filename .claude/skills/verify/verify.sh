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

# ---- Python services: only checks that are configured ----
has_pytest() {
  [ -f "$1/pytest.ini" ] || [ -f "$1/conftest.py" ] ||
    grep -qs '^\[tool\.pytest' "$1/pyproject.toml" ||
    grep -qs '^\[tool:pytest\]' "$1/setup.cfg" ||
    grep -qs '^\[pytest\]' "$1/tox.ini"
}
has_ruff() {
  [ -f "$1/ruff.toml" ] || [ -f "$1/.ruff.toml" ] || grep -qs '^\[tool\.ruff' "$1/pyproject.toml"
}
venv_python() {
  if [ -x "$1/.venv/Scripts/python.exe" ]; then echo "$1/.venv/Scripts/python.exe"
  elif [ -x "$1/.venv/bin/python" ]; then echo "$1/.venv/bin/python"
  fi
}

for svc in backend worker; do
  dir="$ROOT/$svc"
  [ -d "$dir" ] || continue
  py="$(venv_python "$dir")"
  for tool in ruff pytest; do
    if ! "has_$tool" "$dir"; then
      skip "$svc: $tool" "no $tool config"
    elif [ -z "$py" ]; then
      fail "$svc: $tool" "$tool is configured in $svc/ but there is no $svc/.venv to run it with."
    elif [ "$tool" = ruff ]; then
      step "$svc: ruff check" "$dir" "$py" -m ruff check .
    else
      step "$svc: pytest" "$dir" "$py" -m pytest -q
    fi
  done
done

echo "All checks passed."
