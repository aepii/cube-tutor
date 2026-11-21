# CubeTutor — Roadmap

_Last audited 2026-11-14 against the actual code. Updated 2026-11-21: the vision, Phases 10–24, and the switch from Celery to Azure. Supersedes the 2026-08-04 version. Status on `master`: Phases 1, 2 and 5 are done: engine, parser, Expo 58, stickerless rendering, layer turning (PRs #1–#9). **Next up: the architecture track (Phases 4 → 9 → 23 → 24)**, before more features._

**Where to start:** the task checklist is in [§6](#6-task-checklist). §2 lists what's already built. §3–§5 explain the *why* behind the tasks.

## 1. What this project is

An app for learning and practicing speedcubing (OLL / PLL / F2L) with an interactive 3D cube.

**Vision.** The goal is a complete cubing practice tool. It's a resume project, so it has to be worth building and worth explaining even with no users:
- **Learn:** browse algorithms and watch them play on the 3D cube.
- **Practice:** drill specific cases with a per-algorithm timer.
- **Time:** full solves with WCA-style inspection, sessions and averages (ao5 / ao12).
- **Track:** mark algorithms as learning, learned or favorite, and see progress per subset.
- **Contribute:** submit your own algorithms. The server checks that each one actually solves its case before accepting it.
- **Scan:** photograph a real cube and get a step-by-step CFOP solution (Cross → F2L → OLL → PLL).
- **Usable without knowing how to cube:** a guided beginner solve, plus shareable links that open the cube.
- **Compete and improve:** a daily scramble with a leaderboard, live races, a cross trainer, and stage-by-stage analysis of your solves.

The backend carries the parts that really need a server:
- validating submitted algorithms
- solving
- photo processing in the background
- timer sync and stats

It runs on **Azure** (§3.9):
- **Container Apps:** the API, plus a worker fed by an **Azure Service Bus** queue
- **Postgres Flexible Server**, **Blob Storage**, **Static Web Apps** for the web build
- **Bicep** infrastructure, deployed by **GitHub Actions** to separate dev and prod environments

Locally everything runs in Docker Compose with Azure's emulators.

| Part | Stack | Location | State |
|---|---|---|---|
| App | Expo (React Native + web), `@react-three/fiber`, Zustand | `frontend/` | Auth + algorithm list work. Stickerless 3D cube drawn from the engine state; free rotation; layer turning by swipe; animated playback. |
| API | FastAPI + SQLModel + Alembic + Postgres | `backend/` | Auth (register/login/refresh/logout) and favorite/learn endpoints work. Refresh-token storage needs rework (§4). `images.py` is a placeholder. |
| Worker | Celery + Redis today → **Service Bus consumer** (Phase 24) | `backend/app/worker/` | Skeleton: one fake `process_image` task that sleeps 3s. |
| Infra / CI | none today → GitHub Actions + Bicep (Phases 9, 23) | `.github/`, `infra/` | Nothing yet: no CI, no deployment. |
| Scraper | requests + BeautifulSoup → speedcubedb.com | `scraper/` | Done. Produced `shared/data/raw/*.json`: F2L 41 cases / 622 solutions, OLL 57 / 228, PLL 21 / 84. |

---

## 2. What's already built (the foundation)

Everything in §6 builds on these. ✅ = works today.

**Backend**
- ✅ Auth API: `POST /v1/auth/register`, `/login`, `/refresh`, `/logout`; JWT access (15 min) + refresh (7 days) with rotation and revocation — `backend/app/api/routes/auth.py`
- ✅ Algorithms API: `GET /v1/algs/?subset=` (cases + solutions + the user's favorite/learned flags, ordered), idempotent `PUT /v1/algs/{id}/favorite` and `PUT /v1/algs/{id}/learn` taking `{value}` — `routes/algs.py`
- ✅ Models: `User`, `RefreshToken`, `AlgorithmCase`, `AlgorithmSolution`, `UserAlgorithm` — `backend/app/models/`
- ✅ Seed script loads the scraped JSON into Postgres, safe to re-run — `backend/seed/seed_algorithms.py`
- ✅ Scraper + data: 119 cases / 934 solutions in `shared/data/raw/*.json`
- ✅ Docker Compose: backend, Postgres, Redis, pgAdmin, Celery worker
- ⚠️ Celery: wired end to end, but the only task is a fake (`backend/app/worker/tasks.py`). **To be replaced by Service Bus (Phase 24).**
- ❌ No CI, no deployment, no environments

**Frontend**
- ✅ Login / register screens — `app/(auth)/`
- ✅ Auth store with token persistence (SecureStore on native, localStorage on web) and route guarding — `features/auth/`, `app/_layout.tsx`
- ✅ API client attaching the access token — `shared/api/client.ts`
- ✅ Learn tab: algorithm list with favorite / learned toggles (optimistic UI) — `app/(tabs)/learn.tsx`, `features/learn/`
- ✅ Cube engine: 54-sticker model; face, slice, wide and rotation moves; facelet export; random scrambles. Checked against all 934 scraped solutions. Lives in `features/cube/engine/`. _(PR #5)_
- ✅ Parser: wide moves (`r`, `Rw`) and any turn count. Moves keep their notation as written, never normalized (`R2'` stays `R2'`). Lives in `helpers/moveParser.ts`. _(PRs #5, #7)_
- ✅ Stickerless 3D cube (GAN/MoYu style) drawn straight from the engine state, with shared geometry and materials. Lives in `CubeModel.tsx` and `render/`. _(PR #8)_
- ✅ Free rotation via world-axis quaternions, plus pinch zoom
- ✅ Cube state in a Zustand store; the viewer reads from it — `store/useCubeStore.ts`
- ✅ Layer turning: swipe a layer (works in any cube orientation), animated playback with literal turns, move queue. _(PR #9)_
- ❌ No logout button

---

## 3. Core design decisions

### 3.1 Cube engine: use a sticker model, not face arrays + adjacency tables

The 2026-08 roadmap proposed 6 face matrices plus a hand-written table of which strips each move cycles. **Don't.** Instead, represent the cube as 54 stickers:

```ts
type Vec3 = [number, number, number];        // integer coords in {-1, 0, 1}
interface Sticker { pos: Vec3; normal: Vec3; color: Color }
```

A move = pick an axis, the set of layers (coordinate values on that axis), and a quarter-turn count; rotate `pos` and `normal` of every sticker in those layers by an integer 90° rotation matrix.

- Face moves `R` = axis x, layer {1}. Slices `M` = axis x, layer {0}. Wide `r` = axis x, layers {0, 1}. Rotation `x` = axis x, layers {-1, 0, 1}. **No adjacency tables at all.**
- Maps directly onto rendering: the 3D view already works in positions, so the turn animation is "rotate these meshes, then commit new state."
- Derive face matrices / a 54-char facelet string only at the boundaries (scanner input, solver, debugging). Define that facelet convention once, in one place, with a comment.

### 3.2 Engine tests: use cube identities

Hand-deriving expected states is error-prone; identities are not:
- every move followed by its inverse = identity; any move ×4 = identity
- `(R U R' U')` ×6 = identity
- each PLL alg applied N times returns to solved
- **every solution in `shared/data/raw/*.json` must solve its own `setup`** — 934 free test cases

### 3.3 Gestures: one input system, not two

Today react-native-gesture-handler (orbit) and R3F `onPointerDown` (cubie touch) coordinate through a React `orbitalControlsEnabled` state flag — that will race. Use a single RNGH pan: on gesture start, raycast from the touch point; hit a cubie → layer turn, miss → orbit.

### 3.4 Orientation-relative turning

Still valid from the old roadmap: keep one canonical state and convert input from screen space into the cube's own coordinates at input time. Transform the screen-space drag direction by the inverse of the cube group's quaternion (`dir.applyQuaternion(group.quaternion.clone().invert())`) to choose axis + direction. The raycast face normal is already in cube-local space **as long as cubie meshes are rebuilt from state after each turn** (identity local rotation) — if you instead leave meshes rotated after an animation, that stops being true.

### 3.5 One engine, two languages (TypeScript + Python), proven identical

The app needs the engine for animation and practice. The backend needs it too:
- to validate submitted algorithms (Phase 14)
- to run the CFOP solver (Phase 15)
- to check scans (Phase 8)

Running Node inside the Python worker would be awkward, so **port the engine to Python** (`cubetutor_engine`, used by both backend and worker). It's about 300 lines because the sticker model has no lookup tables.

**Proving both engines agree:** a generated fixture file, `shared/fixtures/engine_cases.json`, lists scrambles and algorithms with the expected facelet string for each. Both the Jest and pytest suites must reproduce every expected string, and CI runs both. That shared fixture is what stops the two engines from silently drifting apart.

### 3.6 Practicing one case: setup = the algorithm run backwards

To show a case, apply the **inverse** of one of its solutions to a solved cube, then add a random **top-layer turn** (U, U', U2 or none — cubers call this the AUF) so the case doesn't always appear in the same spot. The solution then has to solve that state, possibly with a final top-layer turn.

What "solved" means depends on the subset:
- **F2L** checks `isF2LSolved`.
- **OLL** checks `isLastLayerOriented`.
- **PLL** checks `isSolved`, allowing a final top-layer turn.

That same check validates submitted algorithms. No setup data is needed beyond the solution itself.

### 3.7 Timer stats live in the database

- A solve is `{ user_id, session_id, ms, penalty (none | +2 | DNF), scramble, kind (full | case), case_id?, created_at, client_id }`.
- **Averages are computed in Postgres.** ao5 and ao12 are cubing's averages of 5 and 12: drop the best and worst time, then average the rest. They're computed with window functions (`ROWS BETWEEN 4 PRECEDING AND CURRENT ROW`), with a DNF counting as the worst time.
  - Single-row lookups (personal bests) use an index on `(user_id, kind, ms)`.
  - Rolling averages are computed by the stats endpoint, not stored.
- **Offline-first:** solves are saved on the device first, then synced to the backend in batches.
  - Each solve has a `client_id` generated on the device, and the endpoint is idempotent on `(user_id, client_id)`, so a retried sync never duplicates a solve.

### 3.8 CFOP solver: search for Cross and F2L, look up OLL and PLL

The solver shows the steps a human would take, not the shortest solution. kociemba stays only as a solvability check.

| Stage | Method |
|---|---|
| **Cross** | IDA* search over the 4 cross edges (≤ 8 moves), with a precomputed pruning table. Optionally try all 6 colors and keep the shortest. |
| **F2L** | Solve the 4 corner-edge pairs one at a time with a depth-limited search (IDA*). Moves may not break the cross or pairs already placed. Order the pairs greedily by shortest solution. |
| **OLL / PLL** | Match the top-layer pattern against the 57 + 21 cases in the database, trying all 4 starting orientations. Show the case name and the database algorithm. |

The output is a staged solution with a label per stage, e.g. "Cross (6) · F2L pair 1 (7) … · OLL 27 Sune · PLL T-perm". It runs as a queued job (Service Bus, §3.10) because the search can take seconds. That's the honest reason for the queue, alongside photo processing.

### 3.9 Architecture on Azure (replaces Celery + self-hosted Redis)

```
            GitHub Actions (OIDC, no stored secrets) ── Bicep ──► Azure
                                                                   │
 Static Web Apps (Expo web build) ──HTTPS──► Container App: api (FastAPI)
                                               │  writes job row      │ send {job_id}
                                               ▼                      ▼
                                 Postgres Flexible Server     Service Bus queue ──(KEDA: scale on queue length, 0..N)
                                 (source of truth)                    │ peek-lock
                                               ▲                      ▼
                                               └──── Container App: worker (solver, scan CV)
                                                         │
                                            Blob Storage (scan photos)   Application Insights (logs, traces)
```

| Need | Azure service | Why this one |
|---|---|---|
| API | **Container Apps** (Consumption) | Containers without managing Kubernetes; scales to zero; same image as local |
| Background jobs | **Service Bus queue** + a worker Container App | Peek-lock, delivery limit, **dead-letter queue**, duplicate detection. Replaces Celery (§3.10). |
| Worker scaling | KEDA Service Bus scaler (built into Container Apps) | Worker runs only while there are messages; 0 replicas when idle |
| Scheduled work (daily scramble) | Container Apps **Job** with a cron trigger | Replaces Celery beat |
| Database | **Postgres Flexible Server** | Free for 12 months at the smallest burstable size (B1ms) |
| Files | **Blob Storage** | Scan photos. Only the id goes through the queue, never image bytes. |
| Web app | **Static Web Apps** (free plan) | Hosts the Expo web build; preview environments for PRs |
| Secrets | **Key Vault** + **managed identities** | Services authenticate to Service Bus and Blob with managed identities via RBAC, so there are **no connection strings**. Key Vault holds the JWT secret and database password. |
| Telemetry | **Application Insights** (OpenTelemetry) | Logs, metrics, traces; free ingestion allowance |
| Images | **GitHub Container Registry** | Free, unlike Azure Container Registry (≈$5/mo) |
| Cache / leaderboards / pub-sub | **Redis**, added only when a phase needs it (14 or 18) | At zero users Postgres is enough. Azure Managed Redis has no free tier (≈$12/mo), so start with a cheap option and name Managed Redis as the production choice. |

**Locally:** Docker Compose runs the same images against the official **Service Bus emulator**, **Azurite** (Blob) and Postgres. The code changes only in configuration, never in branches.

### 3.10 Background jobs on Service Bus (instead of Celery)

Celery's Azure transports are community-maintained and lag behind its Redis and RabbitMQ ones. A direct consumer using the `azure-servicebus` SDK is small and shows the queue's semantics first-hand.

- **A `Job` table is the source of truth:** `id, type, status (pending → running → done | failed), payload, result, error, attempts, user_id, timestamps`. Scans and solves are job types. Clients poll `GET /v1/jobs/{id}` (server-sent events later).
- **Enqueue:** the API commits the `Job` row, then sends `{ job_id, type }`, with the trace context in the message properties.
  - The **gap:** if the commit succeeds but the send fails, the job is stuck as `pending`.
  - The **fix:** a periodic sweeper re-sends stale `pending` jobs. Mention the transactional outbox as the fully correct version.
- **Worker:** receive in peek-lock mode, then:
  1. **Skip** if the job is already `done` (idempotent; Service Bus delivers at least once).
  2. **Renew the lock** during long work.
  3. **Complete** on success.
  4. **Abandon** on a transient error, so it's retried up to the queue's maximum delivery count.
  5. **Dead-letter** on a permanent error.
  
  A small dead-letter drain marks those jobs `failed` with the reason. On SIGTERM the worker finishes the current message before stopping (Container Apps scales in by stopping replicas).
- **A `JobQueue` interface** with `ServiceBusJobQueue` and `InMemoryJobQueue` implementations, so pytest needs neither Azure nor the emulator.

### 3.11 Environments, branching and CI/CD

**Branching (decided): trunk-based with release tags.** No long-lived `dev` and `prod` branches.
- Feature branch → PR → `master` (protected: CI must pass, no direct pushes) → **auto-deploys to `dev`**.
- **Production:** publishing a GitHub Release (`v1.2.0`) runs `deploy-prod`. The GitHub `production` environment requires your approval. It deploys the **same image** that ran in dev (same digest, not rebuilt).
- **Rollback:** re-run the deploy for the previous tag.
- **Why not a `prod` branch:** long-lived branches drift and need merge-backs, and every change takes two PRs. Tags give the same separation plus an audit trail of what shipped when. (If you ever want a `prod` branch anyway, only the workflow trigger changes.)

**Environments:**
- `dev` and `prod`, each in its own resource group, with their own Container Apps environment, Service Bus namespace, storage account, Static Web App, App Insights and managed identity.
- **One shared Postgres server** (in `rg-cubetutor-shared`) with two databases, `cubetutor_dev` and `cubetutor_prod`, because only one B1ms server is free. In a real company prod would get its own server; say so in interviews.

**GitHub Actions:**

| Workflow | Trigger | What it does |
|---|---|---|
| `ci.yml` | PR + push to `master` | Frontend: `npm ci`, `tsc`, `jest`, `expo lint`, `expo export --platform web`. Backend: `ruff`, `pytest` (Postgres service container). Docker builds (no push on PRs). Bicep `build` + lint. Path filters skip unaffected jobs. |
| `deploy.yml` (reusable, input: environment) | called by the two below | Signs in to Azure with OIDC, deploys Bicep, runs the **migration job** (`alembic upgrade head`) and waits, points Container Apps at the new image digest, deploys the web build to Static Web Apps, smoke-tests `/health/ready` |
| `deploy-dev.yml` | push to `master` | Builds and pushes images to GHCR, tagged with the commit SHA, then runs `deploy.yml` for `dev` |
| `deploy-prod.yml` | release published | Runs `deploy.yml` for `production` with the release's image digests (approval required) |
| `infra-whatif.yml` | PR touching `infra/` | Posts `az deployment what-if` output as a PR comment |

- **Supporting setup:**
  - Dependabot for npm, pip, GitHub Actions and Docker.
  - Each environment's identity has a federated credential (`repo:<owner>/cube-tutor:environment:dev` / `:production`), so **no Azure secrets are stored in GitHub**.
- **Mobile (later):** EAS Update channels `dev` / `production` publish JS updates to installed apps; EAS Build for store binaries when needed.

### 3.12 Cost (demo with no users)

| Item | Cost |
|---|---|
| Container Apps scaled to zero | within the always-free monthly grant (180k vCPU-seconds, 360k GiB-seconds, 2M requests) |
| Service Bus Basic | cents (billed per million operations) |
| Postgres B1ms | free for 12 months, then ≈$12–15/mo. If you don't want to pay in year 2, move the database to Neon or Supabase. |
| Static Web Apps | free |
| Blob, Key Vault, App Insights, GitHub Container Registry | free allowances / pennies |
| **Expected** | **≈$0–2/mo in year one** |

**Guardrails:**
- A Cost Management **budget alert at $5**, created by Bicep, so it exists from day one.
- Never keep a minimum of one API replica running (that uses up the free grant).
- No Azure Container Registry.
- No Managed Redis until a phase needs it, and then only while demoing.

---

## 4. Issues

### 4.1 Bugs (verified)

1. ✅ _Fixed in PR #5._ **Parser rejects the app's own data.** `VALID_BASES` has no wide moves. 15 distinct tokens / 725 occurrences in the scraped algs fail: `r' r f' f l l' d' d u u' r2 r2' l2 f2 b`. Also accept `Rw`-style notation and parentheses for robustness.
2. **No tab bar / no navigation.** `frontend/app/(tabs)/_layout.tsx` doesn't exist, so Learn and Playground can't be navigated between. No logout button anywhere (`signOut()` is only called by the 401 interceptor).
3. **Forced re-login every 15 minutes.** Access tokens expire in 15 min (`backend/app/core/security.py`); the frontend discards the refresh token (`login.tsx`, `register.tsx` only read `access_token`; `useAuthStore.signIn` stores one token) and the 401 interceptor (`shared/api/client.ts`) signs out instead of refreshing. Logout never calls `/v1/auth/logout`.
4. **Refresh-token storage is slow and only partially hashed.** `/refresh` and `/logout` load *every* unrevoked token for the user and bcrypt-verify each one (O(n) slow hashes; rows accumulate per login, never cleaned up). bcrypt only reads the first 72 bytes — for a JWT that's the header plus the start of the payload, so the signature is never part of the hash. **Fix:** store `sha256(token)` in the indexed `hashed_token` column and look it up directly; add a cleanup for expired/revoked rows.
5. ✅ _Fixed in 4b (#16)._ **Alembic can't build a fresh DB.** `3d35e0512814_init.py` is empty (`pass`); `e21c1e12ed8e` alters tables no migration creates. It only works because `init_db()` calls `create_all` on startup. **Fix:** remove `create_all`, delete both migrations, autogenerate one baseline, run `alembic upgrade head` on container start.
6. **Backend image broken without the bind mount.** `backend/dockerfile` builds from `./backend`, so `shared/` is never copied, but `routes/images.py` imports `shared.tasks`. The seed script also depends on cwd-relative `shared/data/raw`.
7. ✅ _Fixed in `f8a5636`._ **Face-index comment was wrong.** `cube.types.ts` says 2 = Yellow (Down), 3 = White (Top). Actual code: index = three.js `BoxGeometry` face slot = `+X, -X, +Y, -Y, +Z, -Z` = **R, L, U, D, F, B**, and `geometry.ts` colors 2 = White (Up), 3 = Yellow (Down). Every move table depends on this — fix it before writing any.
8. Smaller:
   - `useAuthStore.signIn` `console.log`s the token.
   - No unique constraint on `UserAlgorithm(user_id, algorithm_id)` → double-tap race creates duplicates. Same for `AlgorithmCase(subset, name, subgroup)`.
   - `GET /v1/algs` has no `ORDER BY` → nondeterministic order; also unpaginated with no subset filter.
   - Register race on duplicate email/username → `IntegrityError` 500 instead of 400.
   - `create_engine(..., echo=True)` logs every SQL statement.
   - `CaseGroup` nests a `FlatList` inside the `learn.tsx` `FlatList` (VirtualizedList warning) and uses `globalStyles.container` (`flex: 1`, `justifyContent: center`) per item.
   - `SolutionDetail` copies props into `useState` once → stale after refetch.
   - ✅ _Fixed in PR #8 (shared geometry)._ `Cubie` creates a new `BufferGeometry` on every hover/state change and never disposes the old one (GPU leak).
   - `CubeCamera` calls `updateProjectionMatrix()` every frame (only needed when projection params change).
   - `app/index.tsx` always redirects to login, then `_layout` bounces logged-in users → flicker.
   - `CaseGroup` orientation tabs have no active styling; `learn.tsx` never renders `loading`; error state has no retry.
   - ~~`MoveModifier` includes `"2'"`; normalize it in the parser.~~ **Reversed (PR #7):** moves keep their notation as written, so playback can show `R2'` as a counter-clockwise half turn and `R3` as 270°. Only the cube state reduces modulo 4.

### 4.2 Refactors

- **Backend + worker:** one Python package, one image, three commands (`alembic upgrade head && python -m seed.seed_algorithms` / `uvicorn` / `celery -A app.worker.celery_app worker`). Removes the `shared/` bind-mount hack and gives the worker access to the SQLModel models it will need for scans.
- **`backend/requirements.txt`, `worker/requirements.txt`, `scraper/requirements.txt` are UTF-16** (PowerShell `pip freeze >`). Convert to UTF-8 and trim: backend has both `psycopg2` and `psycopg2-binary`, plus unused `numpy`, `sentry-sdk`, `fastapi-cloud-cli`, `beautifulsoup4`. Consider `uv` + `pyproject.toml`.
- **Unused frontend deps:** `react-icons`, `@react-navigation/drawer`, `r3f-native-orbitcontrols`, `@react-three/drei`, `expo-haptics`, `react-native-webview`, `expo-image`. NativeWind is configured but no component uses `className` — pick it or `StyleSheet`, not both. `reset-project` script points at a nonexistent `scripts/` dir.
- **Favorite/learn endpoints** are near-duplicates and non-idempotent toggles. Replace with `PUT /v1/algs/{id}/favorite` + `{ "value": bool }` (same for learn) sharing one upsert helper.
- **Server state:** use TanStack Query for algorithms (loading/error/retry/optimistic updates) instead of hand-rolled `useState`.
- **Types:** `FaceIndex` is used for both face slot and color (`Map<FaceIndex, FaceIndex>`). Split into `FaceSlot` and `StickerColor` (mostly moot once on the sticker model).
- Settings: drop deprecated `Field(..., env=...)` and the redundant `load_dotenv()` in `db.py`; move CORS origins to settings.

### 4.3 What's done well (keep it)

- Backend layering (routes / schemas / models / core), Pydantic validation, `SecretStr` passwords, refresh-token rotation with revocation.
- Feature-sliced frontend with extracted constants, typed hooks, small Zustand stores.
- Free rotation premultiplies world-axis quaternions — correct, no gimbal lock.
- `GET /v1/algs` fetches per-user flags with one outer join (no N+1).
- Scraper → JSON → idempotent seed is a clean data pipeline.

---

## 5. Scan pipeline (Service Bus + Blob)

Goal: photograph a physical cube → detect state → show it on the 3D cube → solve it. It runs on the job system from §3.10 / Phase 24.

1. `POST /v1/scans`: accept 6 face images and upload them to **Blob Storage**, then create a `Job` (`type = scan`, `pending`), send `{ job_id }` to Service Bus, and return `202 { job_id }`. **Only the id goes through the queue**, never image bytes.
2. **Postgres is the source of truth** for status (`pending → running → done | failed`, plus `result`, `error`). Client polls `GET /v1/jobs/{id}` (server-sent events later).
3. Worker (OpenCV): locate the 3×3 grid per face, sample 9 stickers, classify colors in CIELAB **calibrated against each face's center sticker** (centers never move — this is what handles lighting). Validate: 9 of each color, then solvability via `kociemba`. Solve with the **CFOP solver** (§3.8, Phase 15) and store the staged solution.
4. Queue behavior comes from Phase 24:
   - peek-lock with lock renewal
   - abandon on transient errors, up to the maximum delivery count
   - dead-letter on bad input (unreadable photos), which marks the job `failed`
   - idempotent on `job_id`
   - the worker scales on queue length (KEDA)
   
   Monitoring: Service Bus metrics and App Insights.
5. UX: a correction screen (tap a sticker to fix its color) before solving — detection will sometimes be wrong.

**Depends on** the engine (§3.1), the Python port (§3.5) and the facelet conversion. Scan output must load into the engine, and the staged solution must be parsed and animated via `applyMove`.

Interview framing: color classification could run on the device. The queue is justified by the slow processing (computer vision plus the solver search) and as a showcase of async architecture. Be upfront about that tradeoff.

---

## 6. Task checklist

Everything is built by Claude Code; you orchestrate and review. **[review closely]** = core logic worth reading line by line and being able to explain in interviews. **[review diff]** = skim the diff and check the "Done when". Each phase lists what it **builds on** and when it's **done**.

Phase numbers are IDs, not order. The recommended order is below the diagram.

**Phases are milestones; PRs are smaller.** A phase may ship as several PRs, marked as sub-steps (**4a**, **4b**, …). Each sub-step is one PR, branched from `master` once its prerequisites have merged (never stacked). Split a phase when one part is a prerequisite for another, when parts need different review levels, or when one diff would be too big to review in one sitting. Phases without sub-steps are one PR. Later phases get sub-steps when they come up.

**Sub-steps become GitHub issues just in time.** `/groom` turns the next 1–3 sub-steps into issues with acceptance criteria. `/work <#>` implements one. This checklist stays the high-level map, and the issue is the spec (see CLAUDE.md "Work items").

| Phase | Builds on |
|---|---|
| 1 Groundwork ✅ · 2 Engine ✅ · 5 Layer turning ✅ | — |
| **4 Backend hardening** (Alembic, one Python package, health checks) | — (needed by **every phase that adds tables or deploys**) |
| **9 CI/CD + environments** | 4 |
| **23 Azure platform** (Bicep, dev + prod, walking skeleton) | 4, 9 |
| **24 Background jobs on Service Bus** (replaces Celery) | 4, 23 |
| 3 Nav + auth · 7 Learn UI | independent |
| 6 Learn ↔ cube | 2, 3, 5 |
| 10 Progress tracking | 4 |
| 11 Solve timer | 4 |
| 12 Algorithm drills | 6, 10, 11 |
| 13 Python engine port | 2, 4 |
| 14 Submitted algorithms | 10, 13 |
| 15 CFOP solver | 13, 24 |
| 8 Scan pipeline | 15, 24 |
| 16 Guided beginner solve | 5 (runs on the device; no backend) |
| 17 Shareable links | 6 |
| 18 Daily scramble + leaderboard | 11, 23 (scheduled job), Redis |
| 19 Observability (full tracing) | 24 (App Insights basics land in 23) |
| 20 Solve stage analysis | 11 |
| 21 Race mode | 11, 23, Redis |
| 22 Cross trainer | 15 |

**Recommended order (architecture first):** **4 → 9 → 23 → 24** (4a–4f → 9a–9b → 23a–23c → 24a–24c) → 3 (3a, 3b) → 6 → 17 → 16 → 10 → 11 → 12 → 13 → 15 → 22 → 14 → 18 → 20 → 8 → 19 → 21, with 7 slotted in whenever.
- **Architecture first, as a "walking skeleton":** CI, dev/prod environments on Azure, and the job queue are built and deployed end to end *before* the features that use them, with only trivial functionality at first. Every feature after that lands on a working pipeline and is live in dev on merge. Interviewers value this more than any single feature, and it's the part that's hard to bolt on later.
- **Then the demo:** 6, 17 and 16 make the app usable and shareable for someone who can't solve a cube.
- **The solver (13 → 15) moves ahead of uploads** so the job queue gets its first real workload early.
- **Scanning stays late:** it's the riskiest piece (camera color detection), and by then the solver behind it already works with manual input.

### Phase 1 — Commit pending groundwork ✅ (`f8a5636`)
- [x] Fix face-index comment in `cube.types.ts`
- [x] Move `jest`, `jest-expo`, `@types/jest` to `devDependencies`
- [x] Stub `applyR` so `tsc` passes
- [x] Commit store, parser, move types, `rotateFaceMatrix`, test, roadmap
- [x] Merge `cube-engine-groundwork` into `master` (PR #1)

### Phase 2 — Cube engine + parser ✅ **[review closely]** (PRs #5/#6, #7, #8)
_Builds on:_ move types + parser (`move.types.ts`, `moveParser.ts`), cube store, Jest setup. _See §3.1, §3.2._
- [x] Write the identity tests first (they fail until the engine exists):
  - [x] each move then its inverse = solved; any move ×4 = solved
  - [x] `(R U R' U')` ×6 = solved
  - [x] every solution in `shared/data/raw/*.json` solves its own `setup` (934 cases)
- [x] Sticker model: `Sticker { pos, normal, color }`, `createSolvedCube()`, `isSolved()`
- [x] Integer 90° rotation matrices for x / y / z axes
- [x] Move table: base → `{ axis, layers, direction }` for `R L U D F B`, `M E S`, `x y z`, and wide `r l u d f b`
- [x] `applyMove(state, move)` and `applyAlgorithm(state, moves)`
- [x] Parser: accept wide moves (lowercase + `Rw`), ignore parentheses. Notation is **kept as written** (`R2'` and `R3` are not normalized; PR #7).
- [x] Connect to the renderer: stickerless pieces drawn straight from the sticker state; old `CubeData` renderer deleted (PR #8)
- [x] Facelet-string export (54 chars, URFDLB order), needed later for kociemba / scans
- [x] Store actions: `applyAlgorithm`, `reset`, `scramble`

**Done when:** all identity tests + the 934-solution data test pass, and a dev-only button that runs `scramble` visibly changes the 3D cube.

### Phase 3 — App navigation + auth fixes **[review diff]**
_Builds on:_ existing auth store, API client, backend `/refresh` + `/logout`. _See §4.1 #2, #3._

Ships as 2 independent PRs (either order).

**3a — Navigation** **[review diff]**
- [ ] Add `app/(tabs)/_layout.tsx` with a Learn / Playground tab bar
- [ ] Fix `app/index.tsx` redirect flicker

**3b — Token refresh + logout** **[review closely: single-flight refresh]**
- [ ] Store `refresh_token` alongside `access_token` on login / register
- [ ] 401 interceptor: refresh once (single in-flight refresh shared by concurrent requests), retry the request, sign out only if refresh fails
- [ ] `checkToken` on startup: if the access token is expired but the refresh token is valid → refresh instead of logging out
- [ ] Logout button that calls `POST /v1/auth/logout` and clears both tokens
- [ ] Remove `console.log(newToken)` from `signIn`

**Done when:** you can stay logged in past 15 minutes, switch tabs, and log out.

### Phase 4 — Backend hardening ✅ **[review diff]** (architecture track, step 1)
_Builds on:_ existing models, auth routes, Docker setup. _See §4.1 #4–6, #8 and §4.2._

Ships as 6 PRs: **4a first** (the safety net); then 4b, 4c, 4d in any order; **4e and 4f after 4b** (they change the schema, so they need migrations).

**4a — Test safety net**
- [x] pytest suite: auth flow + algs endpoints against a test DB
- [x] ruff config, so `/verify` and CI (Phase 9) run it

**4b — Migrations**
- [x] Alembic: remove `create_all` from startup, replace both migrations with one baseline, run `alembic upgrade head` on container start

**4c — Packaging**
- [x] One Python package + one image for backend and worker (two commands); drop the `shared/` bind-mount dependency
- [x] Production-ready Dockerfile: multi-stage, non-root user, no dev dependencies, `uvicorn` settings from env
- [x] Convert `requirements.txt` files to UTF-8 and trim unused packages (or move to `uv` + `pyproject.toml`)
- [x] Seed on container start, after `alembic upgrade head` (idempotent seed with a `main()` guard, reading the packaged raw data instead of the `shared/` bind mount)

**4d — Config + health**
- [x] All config from environment variables (database URL, JWT secret, CORS origins, queue/blob settings), with nothing environment-specific in code (blob settings land with Phase 24, when something reads them)
- [x] Settings: CORS origins from env, SQL `echo` off by default, drop deprecated `Field(env=...)`
- [x] Health endpoints: `/health/live` (process is up) and `/health/ready` (database reachable), used by Container Apps probes and the deploy smoke test

**4e — Auth hardening** (after 4b)
- [x] Refresh tokens: store `sha256(token)`, look up by indexed hash (no bcrypt loop); clean up expired/revoked rows
- [x] Catch `IntegrityError` on register → 400

**4f — Algorithms API** (after 4b)
- [x] Unique constraints: `UserAlgorithm(user_id, algorithm_id)`, `AlgorithmCase(subset, name, subgroup)`, `AlgorithmSolution(case_id, solution)`
- [x] `GET /v1/algs`: `ORDER BY`, optional `?subset=` filter
- [x] Replace toggle endpoints with `PUT /v1/algs/{id}/favorite` / `/learn` taking `{ "value": bool }` (shared upsert helper); update the frontend service

**Done when:** `docker compose up` on an empty DB migrates, seeds, and passes pytest.

### Phase 5 — Layer turning ✅ **[review closely]** (PR #9) (see the 3D migration plan: rendering + input first, turning after Phase 2)
_Builds on:_ **Phase 2 engine** (`applyMove`), existing free rotation (`cubeGroupRef` quaternion). _See §3.3, §3.4._
- [x] Replace the R3F `onPointerDown` + `orbitalControlsEnabled` flag with one RNGH pan that raycasts on start (hit cubie → turn, miss → orbit). Built with gesture-handler 3 hooks; pinch, twist, hover and the web wheel are part of the same gesture tree.
- [x] On drag: project the drag onto the touched face's plane, convert it to cube coordinates with the inverse cube quaternion → axis, layer, direction (`n × u`) → a `Move` (`helpers/screenDrag.ts`, `helpers/turnMath.ts`)
- [x] Animate the affected layer in a pivot group, then commit via `applyMove` and re-render from state. The layer follows the finger and snaps on release; playback animates the literal turns (`R2'`, `R3`).
- [x] Busy lock + move queue in the store so turns don't overlap (`activeTurn`, `queue`)
- [x] Remove the `console.log` in `Cubie.tsx`; dispose old geometries (PR #8)

**Done when:** you can flip the cube upside down, swipe the layer on the right of the screen, and the layer that's visually on the right turns the expected direction.

### Phase 6 — Learn ↔ Playground integration **[review diff]**
_Builds on:_ Phase 2 (`applyAlgorithm`), Phase 5 (animation), Phase 3 (tabs), existing Learn list.
- [ ] Tap a solution in Learn → open the cube with the case's `setup` applied
- [ ] Play / step through the solution move by move with animation; highlight the current move in the notation
- [ ] Playground controls: scramble, reset, undo/redo (move history in the store)

**Done when:** tapping any OLL/PLL/F2L solution plays it on the cube and ends solved.

### Phase 7 — Learn tab polish **[review diff]**
_Builds on:_ existing Learn tab, Phase 4 endpoint changes. Independent of the cube work.
- [ ] TanStack Query for algorithms (loading, error + retry, optimistic updates); remove the `useState` copies in `SolutionDetail`
- [ ] `SectionList` grouped by subset (no nested `FlatList`)
- [ ] Active styling on the F2L orientation tabs
- [ ] Filter by favorited / learned; search by case name
- [ ] Remove unused deps (§4.2); pick NativeWind or `StyleSheet`
- [ ] Later (after Phase 2): small cube thumbnail per case

### Phase 8 — Scan pipeline **[review closely: worker/CV]**, **[review diff: API/infra]**
_Builds on:_ **Phase 2** (facelet import/export, `applyAlgorithm`), **Phase 4** (single backend/worker package, Alembic), **Phase 15** (CFOP solver), **Phase 24** (job queue). _See §5._
- [ ] `POST /v1/scans` (upload 6 images to Blob → create a `scan` job → 202 `{ job_id }`); status via `GET /v1/jobs/{id}`
- [ ] Blob container for scan photos (managed-identity access), size/type limits, lifecycle rule deletes photos after N days
- [ ] `scan` job handler: transient errors are retried, unreadable photos are dead-lettered
- [ ] Worker: grid detection → sample stickers → CIELAB classification calibrated on centers → validate (9 of each color, solvable via `kociemba`) → CFOP solve (Phase 15)
- [ ] Manual entry as a fallback: paint the stickers on a flat cube map, using the same solve path
- [ ] App: camera capture flow (6 faces with an on-screen guide), status polling
- [ ] Sticker correction screen before solving
- [ ] Load the scanned state into the cube and play the solution

**Done when:** you scan a real scrambled cube, correct at most a couple of stickers, and watch it solve.

### Phase 9 — CI/CD + environments **[review closely: workflows]** (architecture track, step 2)
_Builds on:_ Phase 4 (pytest suite, production Dockerfile). _See §3.11._ The deploy steps go live in Phase 23, once there's Azure to deploy to.

Ships as 2 PRs: 9a, then 9b.

**9a — CI**
- [ ] `ci.yml` on every PR and push to `master`: frontend (`tsc`, `jest`, `expo lint`, web export), backend (`ruff`, `pytest` with a Postgres service container), Docker builds, Bicep lint; path filters; dependency caching
- [ ] Branch protection on `master`: PR required, CI must pass, no direct pushes or force-pushes (a repo setting you turn on once 9a's checks exist; not code)

**9b — Images, environments, releases**
- [ ] GitHub environments `dev` and `production` (`production` requires your approval)
- [ ] Images built once per commit, pushed to GHCR tagged with the commit SHA; prod reuses the same digest
- [ ] Deploy workflows (`deploy.yml` reusable; `deploy-dev` on push to `master`; `deploy-prod` on release published), with no Azure steps until Phase 23
- [ ] Release process: `v*` tags, generated release notes, rollback = redeploy the previous tag
- [ ] Dependabot (npm, pip, GitHub Actions, Docker); CI status badge in the README
- [ ] Update `CLAUDE.md`: branching/release flow, how to cut a release

**Done when:** a PR shows green CI checks, merging is blocked when they fail, and every merge to `master` produces images in GHCR.

### Phase 23 — Azure platform: walking skeleton **[review closely: Bicep, identity]** (architecture track, step 3)
_Builds on:_ Phase 4 (health endpoints, env config), Phase 9 (workflows, environments). _See §3.9, §3.11, §3.12._

Ships as 3 PRs in order: 23a → 23b → 23c.

**23a — Infrastructure (provisioned, nothing deployed)** **[review closely: Bicep, identity]**
- [ ] **Budget alert ($5) in Bicep**, created before anything else
- [ ] `infra/` Bicep modules: Container Apps environment + `api` app, Postgres server (shared) + per-environment database, Static Web App, storage account, Key Vault, Log Analytics + App Insights, user-assigned managed identity, RBAC role assignments; `dev.bicepparam` / `prod.bicepparam`
- [ ] GitHub OIDC: federated credentials per environment; Azure IDs stored as environment variables, not secrets
- [ ] `infra-whatif.yml` posts the planned infra changes on PRs
- [ ] One-time bootstrap documented in `infra/README.md` (create resource groups + OIDC identities) — the only manual step

**23b — API deploy**
- [ ] Migrations as a Container Apps Job (`alembic upgrade head`), run and awaited by the deploy before the new API revision takes traffic
- [ ] `api`: health probes, scale 0..N on HTTP traffic, secrets from Key Vault via the managed identity, CORS for the Static Web Apps domain

**23c — Web deploy + telemetry** **[review diff]**
- [ ] Web build on Static Web Apps (dev + prod); `EXPO_PUBLIC_API_URL` per environment; PR preview environments pointed at the dev API
- [ ] App Insights basics: the OpenTelemetry distro in the API (requests, dependencies, exceptions)
- [ ] README: architecture diagram, live dev/prod URLs

**Done when:** merging a PR deploys the API and web app to dev with no manual steps; publishing a release (after your approval) deploys the same images to prod; you can log in on both; the budget alert exists.

### Phase 24 — Background jobs on Service Bus **[review closely]** (architecture track, step 4; replaces Celery)
_Builds on:_ Phase 4, Phase 23. _See §3.10._

Ships as 3 PRs in order: 24a → 24b → 24c. 24a is the core logic and needs no Azure, so it's reviewed on its own.

**24a — Job model + worker core (in-memory)**
- [ ] `Job` model + migration; `GET /v1/jobs/{id}` (only the owner can read it)
- [ ] `JobQueue` interface + `InMemoryJobQueue` (tests)
- [ ] Worker (`python -m app.worker`):
  - peek-lock receive; idempotent on `job_id`; lock renewal
  - complete / abandon (transient) / dead-letter (permanent)
  - stops cleanly on SIGTERM
  - job handlers looked up by `type`
- [ ] Sweeper re-sends stale `pending` jobs
- [ ] First job type: `diagnostic.echo` (proves the pipeline). The solver (Phase 15) is the first real workload.
- [ ] Tests: unit tests with the in-memory queue

**24b — Service Bus locally (emulator)**
- [ ] `ServiceBusJobQueue` implementation of the `JobQueue` interface
- [ ] Dead-letter drain marks jobs `failed`
- [ ] Docker Compose: **Service Bus emulator + Azurite** in; **Celery, Flower and Redis out** (Redis returns when a phase needs it); delete `backend/app/worker/`
- [ ] Tests: an integration test against the emulator in CI (job round-trip; a poison message ends up dead-lettered and the job `failed`)
- [ ] Update `CLAUDE.md` (running locally, layout)

**24c — Service Bus on Azure**
- [ ] Bicep: Service Bus namespace (Basic) + `jobs` queue (max delivery count, lock duration, dead-lettering) per environment; RBAC: API = Data Sender, worker = Data Receiver
- [ ] `worker` Container App with the KEDA Service Bus scaler (0..N replicas)
- [ ] Trace context carried in message properties, so the API request and the worker task show up in one App Insights trace

**Done when:** a job submitted in dev Azure scales the worker up from 0, completes, and scales back down; a deliberately failing job ends `failed` with its error; the same flow passes against the emulator in CI.

### Phase 10 — Progress tracking: learning / learned / favorite **[review diff]**
_Builds on:_ existing `UserAlgorithm` favorite/learned flags and Learn tab; Phase 4 (`PUT` endpoints, unique constraint).
- [ ] Replace the `learned` boolean with a status `new | learning | learned` (migration keeps existing data); favorite stays a separate flag
- [ ] Mark one solution per case as "my algorithm" (the one used in drills and playback)
- [ ] Progress per subset (e.g. "OLL 23/57 learned") from one grouped query
- [ ] Learn tab: status chips and filters (pairs with Phase 7)

**Done when:** you can move a case through new → learning → learned, pick your algorithm for it, and see subset progress.

### Phase 11 — Solve timer + stats **[review closely: stats SQL, sync]**, **[review diff: UI]**
_Builds on:_ `randomScramble`, the 3D cube (shows the scramble), auth. _See §3.7._
- [ ] Timer screen: hold to arm, release to start, tap/space to stop. Optional 15 s WCA inspection (+2 after 15 s, DNF after 17 s).
- [ ] Scramble shown as text and on the 3D cube; next scramble generated while you solve
- [ ] Penalties (+2 / DNF), delete a solve, sessions
- [ ] Solves stored on the device first; batched sync to `POST /v1/solves`, idempotent on `client_id`
- [ ] `Solve` + `Session` models and migration; `GET /v1/stats`: best single, mo3, ao5, ao12 and ao100 (current and best) via window functions
- [ ] pytest for averages: DNF handling, dropping the best and worst time, fewer than N solves
- [ ] Stats view: list plus a simple trend chart
- [ ] (Nice to have) Import/export in csTimer format

**Done when:** solves made offline sync without duplicates, and ao5/ao12 match csTimer on the same times.

### Phase 12 — Algorithm drills **[review closely: case setup, scheduling]**, **[review diff: UI]**
_Builds on:_ Phase 6 (case on the cube), Phase 10 (status and "my algorithm"), Phase 11 (timer and `Solve` with `kind = case`). _See §3.6._
- [ ] Drill set: choose subsets, cases or "everything I'm learning"
- [ ] For each case: set up the inverse of the algorithm plus a random top-layer turn, timer starts on first touch, stop when done. Store a `Solve` with `case_id`.
- [ ] Reveal: show the algorithm and animate it if you got stuck ("I didn't know it" counts as a fail)
- [ ] Scheduling: weak and slow cases come back more often (start with a simple weighted queue; spaced repetition with SM-2 later)
- [ ] Per-case stats: average time, history, "slowest 5 cases"
- [ ] Recognition-only mode: show the case for a moment, user picks its name from options

**Done when:** a drill session over your "learning" OLLs schedules slow cases more often and records times per case.

### Phase 13 — Python engine port **[review closely]**
_Builds on:_ Phase 2 (TS engine is the reference), Phase 4 (single Python package). _See §3.5._
- [ ] `cubetutor_engine` Python package: stickers, `MOVE_TABLE`, `apply_move`, parser (same notation rules, no normalization), facelets, `is_f2l_solved`, `is_last_layer_oriented`
- [ ] Shared fixtures `shared/fixtures/engine_cases.json` (scramble/algorithm → facelet string), generated by a script from the TS engine
- [ ] Jest **and** pytest both check against the fixtures, in CI
- [ ] The 934-solution data test, in pytest

**Done when:** both suites pass on the same fixture file, and changing a move in one engine fails CI.

### Phase 14 — User-submitted algorithms **[review closely: validation]**, **[review diff: API/UI]**
_Builds on:_ Phase 13 (server-side engine), Phase 10, Phase 4. _See §3.6._
- [ ] `POST /v1/cases/{id}/solutions`: parse, then **verify it solves the case** (same per-subset check as drills, allowing a final top-layer turn). Reject with a clear reason.
- [ ] Normalize for duplicate detection only (stored notation stays as written); reject exact duplicates
- [ ] Move counts (HTM / STM) computed on save; shown next to every algorithm
- [ ] Visibility: private (only me) or public. Upvotes; sort a case's solutions by votes or move count.
- [ ] Rate limiting on submissions, per user. Postgres (count in the last hour) is enough now. Move it to Redis once Redis exists (Phase 18).
- [ ] App: "Add algorithm" on a case with live validation (the TS engine validates on the device first; the server has the final say)

**Done when:** a wrong algorithm is rejected with a reason, a correct one appears in your list, and the same submission validates the same way on the device and the server.

### Phase 15 — CFOP solver **[review closely]**
_Builds on:_ Phase 13 (Python engine), Phase 24 (job queue + worker), algorithm database (OLL/PLL lookup). _See §3.8._
- [ ] Cross: IDA* with a pruning table built offline (cached, loaded once per worker process)
- [ ] F2L: pair-by-pair depth-limited search that preserves solved pieces; greedy pair order
- [ ] OLL/PLL: pattern lookup against the database, allowing for top-layer turns; uses your "my algorithm" choice when available
- [ ] `POST /v1/solver` (state or scramble) → `202 { job_id }`; `GET /v1/jobs/{id}` returns the staged solution. `solve` job handler with a time limit; the result is stored on the job.
- [ ] App: enter a scramble (or paint the stickers by hand), see each stage labeled, play it on the cube stage by stage
- [ ] Tests: 1,000 random scrambles all solve; stage invariants hold (cross intact after F2L, etc.); time limits honored

**Done when:** any scramble returns a labeled CFOP solution within a few seconds that, played on the cube, ends solved.

### Phase 16 — Guided beginner solve **[review closely: step logic]**, **[review diff: UI]**
_Builds on:_ Phase 5 (turning + playback), engine checks. Runs entirely on the device, so it works offline and before any backend phase.

**Why:** most reviewers can't solve a cube. "Solve it with me" makes the demo usable by anyone in a couple of minutes.

**How:** the beginner method (layer by layer), driven by rules rather than search. Each step:
1. finds which known case the cube is in, using engine checks (`isCrossSolved`, "white corner in the top layer", and so on);
2. picks the step's short fixed algorithm;
3. animates it, then repeats until the step's goal is met.

- [ ] Engine checks per beginner step: daisy/cross, first-layer corners, second-layer edges, yellow cross, yellow edges, yellow corners positioned, yellow corners oriented
- [ ] A step engine: `nextStep(state) → { stage, explanation, moves }`, a pure function with unit tests
- [ ] Guided UI: explain the step, play it (or let the user do it), highlight the pieces involved, step back/forward
- [ ] Start from a random scramble or the current cube state (later: from a scan)
- [ ] Tests: 1,000 random scrambles all reach solved within a bounded number of steps

**Done when:** a non-cuber can scramble and follow the guide to a solved cube without reading anything else.

### Phase 17 — Shareable links **[review diff]**
_Builds on:_ Phase 6 (playback), expo-router.
- [ ] `/cube?alg=…`, `/cube?scramble=…` and `/case/{id}`, with links opening the cube and animating it (web build first; deep links on mobile)
- [ ] URL-safe encoding of notation (`'` and spaces); invalid input shows the parse error instead of crashing
- [ ] "Copy link" on any algorithm, scramble or solve
- [ ] (Nice to have) An Open Graph preview image of the cube for shared links

**Done when:** pasting a link into a new browser tab opens the cube and plays the algorithm.

### Phase 18 — Daily scramble + leaderboard **[review closely: Redis/data model]**, **[review diff: UI]**
_Builds on:_ Phase 11 (timer, `Solve`), Phase 23 (Container Apps Jobs, Bicep). **Adds Redis to the platform** (§3.9: the cheapest option for the demo, with Azure Managed Redis named as the production choice).
- [ ] Container Apps **scheduled job** (cron, 00:00 UTC) creates the day's scramble (stored in Postgres; idempotent per date)
- [ ] One attempt per user per day (unique `(user_id, date)`), timed with the normal timer, including inspection
- [ ] Leaderboard in a Redis sorted set (`ZADD daily:{date}`, `ZRANGE`, `ZRANK` for "your rank"), rebuilt from Postgres if Redis loses it. **Postgres stays the source of truth.**
- [ ] Results screen: rank, percentile, top 10, friends later
- [ ] Be honest that times are self-reported and unverifiable; reject sub-3-second times; (later) a smart-cube-verified tag

**Done when:** two accounts solve the same daily scramble and see each other ranked; flushing Redis and rebuilding gives the same board.

### Phase 19 — Observability **[review diff]**
_Builds on:_ Phase 24 (requests that go API → Service Bus → worker), Phase 23 (App Insights basics), Phase 15 or 8 (real workloads to look at).
- [ ] OpenTelemetry across FastAPI, SQLAlchemy, Service Bus and the worker. The trace context travels in message properties, so one trace in App Insights covers the API request, the time spent in the queue **and** the worker task.
- [ ] Locally: the Aspire dashboard or Jaeger in Compose for viewing the same traces
- [ ] Metrics: request latency and error rate, queue depth, dead-letter count, job duration/failures, solver time. Plus an **Azure Workbook** dashboard and **alerts** (dead-letter count > 0, error rate), both defined in Bicep.
- [ ] Structured JSON logs that include the trace id
- [ ] README screenshot: one scan request's trace across the API, the queue and the worker

**Done when:** you can open a trace for one solve request and see time spent in the API, waiting in the queue, and in the worker.

### Phase 20 — Solve stage analysis **[review closely: stage detection]**, **[review diff: UI]**
_Builds on:_ Phase 11 (timer, `Solve`), engine checks (shared with Phase 16).
- [ ] **Split times:** optional stage splits during a solve (web: press space at the end of each stage; mobile: tap zones). Stored with the solve.
- [ ] **Reconstruction:** type in the moves you actually did. The engine replays them and finds where each stage ended (cross, F2L pairs, OLL, PLL), giving **move counts** per stage and which OLL/PLL case came up.
- [ ] Stats: average share of time or moves per stage ("F2L is 58% of your solve"), and how often each OLL/PLL case comes up and how long you take on it (feeds the Phase 12 drills)
- [ ] Engine: `isCrossSolved`, `f2lPairsSolved(state) → number`

**Done when:** a reconstructed solve shows per-stage move counts and case names, and stats show which stage you should practice.

### Phase 21 — Race mode **[review closely: real-time/state]**, **[review diff: UI]**
_Builds on:_ Phase 11 (timer), Phase 23 (deployment), Redis (from Phase 18).
- [ ] Rooms: create or join by code; the room's state lives in Redis with an expiry
- [ ] FastAPI WebSockets: players connect; **Redis pub/sub** relays events across API instances
- [ ] Flow: everyone ready → server picks the scramble → countdown → live "solving / done (time)" → results; rounds repeat; results stored as `Solve`s
- [ ] Server-authoritative state (the server decides start and order; clients only report events); reconnect handling; heartbeats
- [ ] Run 2 API replicas (in Compose and in dev Azure) to prove pub/sub works across them
- [ ] Load test with Locust/k6 (rooms × players), results in the README

**Done when:** two browsers connected to different API instances race in the same room and see each other's results live.

### Phase 22 — Cross trainer **[review diff]**
_Builds on:_ Phase 15 (cross search).
- [ ] Endpoint returns the scramble plus the shortest cross for each of the 6 colors (or just white). It's **synchronous**: cross search takes milliseconds, so no queue. Interview point: the same solver runs synchronously here and as a queued job for full solves, depending on how long it takes.
- [ ] Flow: show the scramble on the 3D cube → 15-second planning timer → type or turn your planned cross → compare with the shortest (move count, sequence animated)
- [ ] Stats: average gap between your cross and the shortest; difficulty filter (shortest cross of N moves)

**Done when:** you can plan a cross in 15 seconds and see how many moves longer it was than the shortest.

### Parked ideas (not planned)
- **Smart cube over Bluetooth** (GAN / MoYu): the 3D cube mirrors the real one, the timer starts and stops itself, drills grade themselves. Start with Web Bluetooth on web; on a phone it needs a custom Expo build (it won't run in Expo Go). Would make Phases 12, 18 and 20 automatic.
- **4×4 and bigger cubes:** extend the engine and renderer to any cube size.
- **Polish:** colorblind palette, haptics on each turn, offline-capable web app (PWA), finger-trick hints.

