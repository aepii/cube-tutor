# CubeTutor

App for learning speedcubing algorithms (OLL / PLL / F2L) with an interactive 3D cube. Resume project; it runs on **web and mobile** from one codebase. The phased task checklist and design decisions are in `ROADMAP.md` (§6 is the checklist; keep its checkboxes current).

More instructions load only when relevant: `frontend/CLAUDE.md`, `backend/CLAUDE.md`, and the path-scoped rules in `.claude/rules/`.

## Working with the user

- The user is an experienced engineer who **orchestrates and reviews**; Claude builds features end to end, including core logic. Don't leave "you write this" stubs.
- **Never commit, push, or open a PR until the user has tested the change locally and says so.** Finish the work, verify it (`/verify` skill), then stop and list exactly what to test by hand.
- **One branch and one PR per feature / unit of work, always branched from `master`** (unless the user says otherwise). A ROADMAP phase can span several PRs; its sub-steps (4a, 4b, …) are the units, each branched from `master` after its prerequisites merge. Don't stack PRs on other feature branches: on this repo, stacked PRs merged into their stale base branches instead of `master` (PRs #2–#5 had to be re-landed). If work truly depends on something unmerged, ask first.
- PRs (branch check, description with close-review vs. skim): `/pr` skill.
- Explain key design choices briefly; the user needs to be able to talk about them.

## Work items (ROADMAP → issue → PR)

`ROADMAP.md` is the strategy and keeps changing. **GitHub issues are the specs**, written just in time, 1–3 ahead, never a whole phase up front.

1. `/groom <step | idea>`: research, then draft issues (Context, Scope, Out of scope, AC, Test plan, Dependencies). The user approves, then they're created with labels and blocked-by links.
2. `/work <issue#>`: load the issue + comments + links, branch `<type>/<#>-<slug>` from `master`, plan (user approves), build, `/verify`, hand off a manual test list mapped to the AC. No commit.
3. The user tests by hand, then `/pr` (`Closes #N`, AC checklist, ROADMAP ticks).

- **Definition of Ready:** the issue has testable AC, a test plan, no open blockers, and no unanswered open questions. Otherwise refine it with `/groom` before `/work`.
- **Definition of Done:** every AC met or changed by agreement (recorded as an issue comment, with the body edited to match), `/verify` passes, docs updated, ROADMAP §6 ticked, and the user tested it by hand.
- **Scope changes** go to the issue (comment + body edit), not just chat. Out-of-scope findings become proposed follow-up issues, not drive-by fixes.
- Labels: type (`enhancement`, `bug`, `chore`, `spike`, `documentation`), `review:closely` / `review:diff`, `area:*`, `phase:N`, `needs:design` (UI work before `docs/ui.md` exists).

## Branching and releases

Trunk-based ([ADR 0006](docs/decisions/0006-trunk-based-release-tags.md); details in `docs/ci-cd.md`):

- **Merging:** feature branch → PR → `master`. `master` is protected: changes arrive only through a PR, the `ci-ok` check must pass, and force-pushes are blocked. The branch is deleted when the PR closes.
- **Dev deploys:** every merge to `master` builds the backend image once (`ghcr.io/aepii/cubetutor-backend:<sha>`) and deploys it to `dev`.
- **Releasing:** publish a GitHub Release with a new `vX.Y.Z` tag on `master` and click *Generate release notes*. `deploy-prod` then promotes that commit's image digest to `production`, after the owner approves. Nothing is rebuilt.
- **Rolling back:** re-run the previous release's `Deploy production` run.
- **No `prod` or release branches.** Don't push or tag from a feature branch.

## Layout

| Path | What |
|---|---|
| `frontend/` | Expo (SDK 58, React Native 0.88, react-native-web), expo-router, Zustand, react-three-fiber |
| `frontend/features/<feature>/` | Feature folders: `components/`, `hooks/`, `helpers/`, `store/`, `types/`, `constants/`, `services/` |
| `frontend/features/cube/engine/` | Pure-TS cube engine (sticker model). No React/three imports here. |
| `frontend/tests/` | Jest tests |
| `backend/` | One uv package + image: FastAPI + SQLModel + Alembic + Postgres (auth, algorithms API), Celery worker in `app/worker/` (Redis broker), seed |
| `shared/data/raw/` | Scraped algorithms JSON (seeded into Postgres, read by the frontend engine tests) |
| `scraper/` | One-off speedcubedb.com scraper that produced the JSON |
| `infra/` | Bicep for Azure: `bootstrap.bicep` (once, Cloud Shell) and `main.bicep` (per environment, applied by `deploy.yml`) |

## Docs

`docs/` describes the system as built (plans stay in `ROADMAP.md`). Read the relevant one before changing that area. Docs ship in the same PR as the code:

- Behavior changes → update the doc that describes it.
- New feature → add a section to the relevant doc, or a new doc plus a line below.
- New significant choice (framework, data model, storage/queue, reversing an earlier choice) → new ADR in `docs/decisions/`; mark any ADR it reverses as superseded.

`/pr` checks this before drafting. Which doc covers what:

- `docs/architecture.md`: components, scrape → seed → API → app flow. Start here for cross-cutting work.
- `docs/cube-engine.md`: sticker model, move application, literal turns vs. state. Before touching `features/cube/engine/`, the parser, or the turn queue.
- `docs/rendering.md`: R3F setup, fiber split, demand frameloop, gestures and turn animation. Before touching cube components, input, or `render/`.
- `docs/backend.md`: tables, auth flow, endpoint list, migration status. Before touching `backend/` or frontend API/auth code.
- `docs/data-pipeline.md`: scraper, raw JSON shape, seeding, Celery. Before touching `scraper/`, `shared/data/`, `backend/app/worker/`, or the seed.
- `docs/ci-cd.md`: GitHub Actions (CI and the `ci-ok` check, image build, deploy workflows), `master` ruleset, environments, releases and rollback, Dependabot. Before touching `.github/` or cutting a release.
- `docs/infra.md`: Azure resources per environment, deploy identities and RBAC, naming, region, cost guardrails. Before touching `infra/` or the Azure steps in `deploy.yml` / `infra-whatif.yml` (bootstrap runbook: `infra/README.md`).
- `docs/decisions/`: ADRs. When a change would revisit Expo, Zustand, the sticker model, Celery, the branching/release flow, or the Azure platform (Container Apps, Bicep, OIDC identities).

## Running

```powershell
docker compose up -d                 # migrate+seed (one-shot), then backend :8000 (/docs) and Celery; Postgres :5433, Redis, pgAdmin :5050
cd frontend; npm run web             # http://localhost:8081
cd frontend; npm start               # Expo Go on a phone (set EXPO_PUBLIC_API_URL in frontend/.env to the PC's LAN IP)
```

- **Node 24 LTS** is the target (Node 23 is EOL; Jest 30 doesn't support it).
