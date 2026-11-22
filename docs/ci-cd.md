# CI/CD

GitHub Actions workflows live in [`.github/workflows/`](../.github/workflows/). Design and the full target pipeline: ROADMAP §3.11. This doc covers what exists today: the CI gate, `master` protection and branch cleanup (9a). Images, environments and releases arrive in 9b.

## CI (`ci.yml`)

Runs on every pull request and every push to `master`. Permissions: `contents: read`. A newer push to the same PR cancels the older run; pushes to `master` always run to completion.

| Job | Runs when these change | Steps |
|---|---|---|
| `changes` | always | [`dorny/paths-filter`](https://github.com/dorny/paths-filter) decides which jobs below run |
| `frontend` | `frontend/**`, `shared/**`, `.nvmrc` | Node from `.nvmrc` (24), `npm ci` (npm cache), `tsc --noEmit`, `jest --ci`, `expo lint`, `expo export --platform web` |
| `backend` | `backend/**`, `shared/**` | uv (cache keyed on `backend/uv.lock`), Python 3.12, `uv sync --locked`, `ruff check`, `pytest` against a `postgres:18` service container |
| `docker` | `backend/**`, `shared/data/**`, `.dockerignore` | Builds `backend/Dockerfile` (context = repo root) with buildx and the GHA layer cache; **no push** |
| `ci-ok` | always | Fails if any job above failed or was cancelled; skipped jobs count as passing |

Every filter also matches `.github/workflows/ci.yml`, so a change to CI runs every job. `shared/**` feeds both sides: the engine tests read `shared/data/raw`, and so do the seed and the image.

**Why one aggregate check.** The ruleset requires only `ci-ok`. If each job were required and skipped by a workflow-level `paths:` filter, GitHub would wait forever for a check that never reports. Filtering inside the workflow and aggregating avoids that. When adding a job, add it to `ci-ok`'s `needs`, or it won't gate merges.

**Backend tests in CI.** `backend/tests/conftest.py` prefers `TEST_DATABASE_URL` (set by the job to `…/cubetutor_test` on the service container), creates that database if it's missing, and sets the remaining required settings, so CI uses no `.env`.

**Action pinning.** Third-party actions are pinned to a commit SHA with the release tag in a comment (`@<sha> # v7.0.1`). Tags can be moved; SHAs can't. Bump them by resolving the new tag's SHA (`gh api repos/<owner>/<action>/commits/<tag> --jq .sha`); Dependabot will do this from 9b.

### Reproducing a failure locally

CI runs the same commands as [`/verify`](../.claude/skills/verify/SKILL.md) (which also runs an Android export). Run `bash .claude/skills/verify/verify.sh`, or the single step from the table in `frontend/` or `backend/`. The backend tests need Compose Postgres up (`docker compose up -d postgres`). The image: `docker build -f backend/Dockerfile .` from the repo root.

## `master` protection

A repository ruleset, kept as code in [`.github/rulesets/master.json`](../.github/rulesets/master.json):

- changes reach `master` only through a pull request (0 approvals required; this is a solo repo)
- `ci-ok` must pass; branches don't have to be up to date with `master` before merging
- no force-pushes, no deleting `master`
- **no bypass actors**: this applies to admins too

Applying or updating it (repo admin, once):

```bash
# create
gh api -X POST repos/{owner}/{repo}/rulesets --input .github/rulesets/master.json
# update after editing the file
id=$(gh api repos/{owner}/{repo}/rulesets --jq '.[] | select(.name=="master") | .id')
gh api -X PUT repos/{owner}/{repo}/rulesets/$id --input .github/rulesets/master.json
```

The required check name must match the `ci-ok` job's `name:`. Rename one and you must rename the other, or every PR waits for a check that never comes.

## Branch cleanup

- **Merged PRs:** the repo setting "Automatically delete head branches" deletes the branch. Turn it on with `gh api -X PATCH repos/{owner}/{repo} -F delete_branch_on_merge=true`.
- **PRs closed without merging:** [`cleanup-branch.yml`](../.github/workflows/cleanup-branch.yml) deletes the head branch, but only for branches in this repo (never a fork's) and never `master`. It runs on `pull_request` (not `pull_request_target`) with `contents: write`, and passes the branch name through an env var so it is never interpolated into the shell.
- A deleted branch can be restored from the PR page ("Restore branch").
- Locally, prune the deleted remote branches with `git fetch --prune` (or `git config fetch.prune true`).
