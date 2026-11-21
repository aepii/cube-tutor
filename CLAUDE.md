# CubeTutor

App for learning speedcubing algorithms (OLL / PLL / F2L) with an interactive 3D cube. Resume project; it runs on **web and mobile** from one codebase. The phased task checklist and design decisions are in `ROADMAP.md` (§6 is the checklist; keep its checkboxes current).

More instructions load only when relevant: `frontend/CLAUDE.md`, `backend/CLAUDE.md`, and the path-scoped rules in `.claude/rules/`.

## Working with the user

- The user is an experienced engineer who **orchestrates and reviews**; Claude builds features end to end, including core logic. Don't leave "you write this" stubs.
- **Never commit, push, or open a PR until the user has tested the change locally and says so.** Finish the work, verify it (`/verify` skill), then stop and list exactly what to test by hand.
- **One branch and one PR per feature / unit of work, always branched from `master`** (unless the user says otherwise). A ROADMAP phase can span several PRs; its sub-steps (4a, 4b, …) are the units, each branched from `master` after its prerequisites merge. Don't stack PRs on other feature branches: on this repo, stacked PRs merged into their stale base branches instead of `master` (PRs #2–#5 had to be re-landed). If work truly depends on something unmerged, ask first.
- PRs (branch check, description with close-review vs. skim): `/pr` skill.
- Explain key design choices briefly; the user needs to be able to talk about them.

## Layout

| Path | What |
|---|---|
| `frontend/` | Expo (SDK 58, React Native 0.88, react-native-web), expo-router, Zustand, react-three-fiber |
| `frontend/features/<feature>/` | Feature folders: `components/`, `hooks/`, `helpers/`, `store/`, `types/`, `constants/`, `services/` |
| `frontend/features/cube/engine/` | Pure-TS cube engine (sticker model). No React/three imports here. |
| `frontend/tests/` | Jest tests |
| `backend/` | FastAPI + SQLModel + Alembic + Postgres (auth, algorithms API) |
| `worker/`, `shared/` | Celery worker + tasks (Redis broker); `shared/data/raw/*.json` = scraped algorithms |
| `scraper/` | One-off speedcubedb.com scraper that produced the JSON |

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
- `docs/data-pipeline.md`: scraper, raw JSON shape, seeding, Celery. Before touching `scraper/`, `shared/`, `worker/`, or the seed.
- `docs/decisions/`: ADRs. When a change would revisit Expo, Zustand, the sticker model, or Celery.

## Running

```powershell
docker compose up -d                 # backend :8000 (/docs), Postgres :5433, Redis, pgAdmin :5050, Celery
cd frontend; npm run web             # http://localhost:8081
cd frontend; npm start               # Expo Go on a phone (set EXPO_PUBLIC_API_URL in frontend/.env to the PC's LAN IP)
```

- **Node 24 LTS** is the target (Node 23 is EOL; Jest 30 doesn't support it).
