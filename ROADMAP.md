# CubeTutor — Roadmap

_Last audited 2026-11-14 against the actual code. Supersedes the 2026-08-04 version. Current state: `npx tsc --noEmit` passes, `npx jest` passes (1 test). Branch `cube-engine-groundwork`._

**Where to start:** the task checklist is in [§6](#6-task-checklist). §2 lists what's already built. §3–§5 explain the *why* behind the tasks.

## 1. What this project is

An app that teaches speedcubing algorithms (OLL / PLL / F2L) with an interactive 3D cube.

| Part | Stack | Location | State |
|---|---|---|---|
| App | Expo (React Native + web), `@react-three/fiber`, Zustand | `frontend/` | Auth + algorithm list work. 3D cube renders and free-rotates. **Layer turning is 0% wired.** No tab bar. |
| API | FastAPI + SQLModel + Alembic + Postgres | `backend/` | Auth (register/login/refresh/logout) and favorite/learn endpoints work. Refresh-token storage needs rework (§4). `images.py` is a placeholder. |
| Worker | Celery + Redis | `worker/`, `shared/` | Skeleton: one fake `process_image` task that sleeps 3s. |
| Scraper | requests + BeautifulSoup → speedcubedb.com | `scraper/` | Done. Produced `shared/data/raw/*.json`: F2L 41 cases / 622 solutions, OLL 57 / 228, PLL 21 / 84. |

---

## 2. What's already built (the foundation)

Everything in §6 builds on these. ✅ = works today.

**Backend**
- ✅ Auth API: `POST /v1/auth/register`, `/login`, `/refresh`, `/logout`; JWT access (15 min) + refresh (7 days) with rotation and revocation — `backend/app/api/routes/auth.py`
- ✅ Algorithms API: `GET /v1/algs/` (cases + solutions + the user's favorite/learned flags), `POST /v1/algs/{id}/favorite`, `POST /v1/algs/{id}/learn` — `routes/algs.py`
- ✅ Models: `User`, `RefreshToken`, `AlgorithmCase`, `AlgorithmSolution`, `UserAlgorithm` — `backend/app/models/`
- ✅ Seed script loads the scraped JSON into Postgres, safe to re-run — `backend/seed/seed_algorithms.py`
- ✅ Scraper + data: 119 cases / 934 solutions in `shared/data/raw/*.json`
- ✅ Docker Compose: backend, Postgres, Redis, pgAdmin, Celery worker
- ⚠️ Celery: wired end to end, but the only task is a fake (`shared/tasks.py`)

**Frontend**
- ✅ Login / register screens — `app/(auth)/`
- ✅ Auth store with token persistence (SecureStore on native, localStorage on web) and route guarding — `features/auth/`, `app/_layout.tsx`
- ✅ API client attaching the access token — `shared/api/client.ts`
- ✅ Learn tab: algorithm list with favorite / learned toggles (optimistic UI) — `app/(tabs)/learn.tsx`, `features/learn/`
- ✅ 3D cube renders from a `CubeData` state (27 cubies, per-face vertex colors) — `features/cube/helpers/math.ts`, `geometry.ts`
- ✅ Free rotation (drag, two-finger twist) via world-axis quaternions, pinch zoom — `hooks/useCubeGestures.ts`, `useCubeRotation.ts`
- ✅ Cube state in a Zustand store; the viewer reads from it — `store/useCubeStore.ts`
- ✅ Move notation types + parser (`"R U R' U'"` → `Move[]`) — `helpers/moveParser.ts` ⚠️ no wide moves yet
- ✅ `rotateFaceMatrix` + 1 Jest test — `helpers/cubeState.ts`, `tests/`
- ❌ Layer turning: `useCubeTurn` is empty, `applyR` is a stub, `Cubie` only logs on touch
- ❌ No tab bar, no logout button

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

---

## 4. Issues

### 4.1 Bugs (verified)

1. **Parser rejects the app's own data.** `VALID_BASES` has no wide moves. 15 distinct tokens / 725 occurrences in the scraped algs fail: `r' r f' f l l' d' d u u' r2 r2' l2 f2 b`. Also accept `Rw`-style notation and parentheses for robustness.
2. **No tab bar / no navigation.** `frontend/app/(tabs)/_layout.tsx` doesn't exist, so Learn and Playground can't be navigated between. No logout button anywhere (`signOut()` is only called by the 401 interceptor).
3. **Forced re-login every 15 minutes.** Access tokens expire in 15 min (`backend/app/core/security.py`); the frontend discards the refresh token (`login.tsx`, `register.tsx` only read `access_token`; `useAuthStore.signIn` stores one token) and the 401 interceptor (`shared/api/client.ts`) signs out instead of refreshing. Logout never calls `/v1/auth/logout`.
4. **Refresh-token storage is slow and only partially hashed.** `/refresh` and `/logout` load *every* unrevoked token for the user and bcrypt-verify each one (O(n) slow hashes; rows accumulate per login, never cleaned up). bcrypt only reads the first 72 bytes — for a JWT that's the header plus the start of the payload, so the signature is never part of the hash. **Fix:** store `sha256(token)` in the indexed `hashed_token` column and look it up directly; add a cleanup for expired/revoked rows.
5. **Alembic can't build a fresh DB.** `3d35e0512814_init.py` is empty (`pass`); `e21c1e12ed8e` alters tables no migration creates. It only works because `init_db()` calls `create_all` on startup. **Fix:** remove `create_all`, delete both migrations, autogenerate one baseline, run `alembic upgrade head` on container start.
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
   - `Cubie` creates a new `BufferGeometry` on every hover/state change and never disposes the old one (GPU leak).
   - `CubeCamera` calls `updateProjectionMatrix()` every frame (only needed when projection params change).
   - `app/index.tsx` always redirects to login, then `_layout` bounces logged-in users → flicker.
   - `CaseGroup` orientation tabs have no active styling; `learn.tsx` never renders `loading`; error state has no retry.
   - `MoveModifier` includes `"2'"`, which is identical to `"2"` physically — normalize in the parser.

### 4.2 Refactors

- **Backend + worker:** one Python package, one image, two commands (`uvicorn` / `celery -A ...`). Removes the `shared/` bind-mount hack and gives the worker access to the SQLModel models it will need for scans.
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

## 5. Scan pipeline (Redis + Celery)

Goal: photograph a physical cube → detect state → show it on the 3D cube → solve it.

1. `POST /v1/scans` — accept 6 face images; store them (volume or MinIO); create a `Scan` row (`pending`); enqueue `process_scan(scan_id)`; return `202 { scan_id }`. **Only the id goes through Redis**, never image bytes.
2. **Postgres is the source of truth** for status (`pending → processing → done | failed`, plus `result`, `error`). Client polls `GET /v1/scans/{id}` (SSE later). Don't rely on Celery's result backend — results expire and can't be queried per user.
3. Worker (OpenCV): locate the 3×3 grid per face, sample 9 stickers, classify colors in CIELAB **calibrated against each face's center sticker** (centers never move — this is what handles lighting). Validate: 9 of each color, then solvability via `kociemba`; solve; store the solution string.
4. Celery config: `task_acks_late=True`, `worker_prefetch_multiplier=1`, soft/hard time limits, `autoretry_for` transient errors with backoff only, dedicated `scans` queue, idempotent on `scan_id`, Flower for monitoring.
5. UX: a correction screen (tap a sticker to fix its color) before solving — detection will sometimes be wrong.

**Depends on** the engine (§3.1) and the facelet conversion: scan output must load into the engine, and the kociemba solution (URFDLB facelet order) must be parsed and animated via `applyMove`.

Interview framing: color classification could run on-device; the queue is justified as async/heavy processing and as an async-architecture showcase. Be upfront about that tradeoff.

---

## 6. Task checklist

Everything is built by Claude Code; you orchestrate and review. **[review closely]** = core logic worth reading line by line and being able to explain in interviews. **[review diff]** = skim the diff and check the "Done when". Each phase lists what it **builds on** and when it's **done**.

```
Phase 1 (groundwork) ──► Phase 2 (engine) ──► Phase 5 (layer turning) ──► Phase 6 (Learn ↔ cube)
                                    │                                            │
                                    └──────────────► Phase 8 (scan pipeline) ◄───┘
Phase 3 (nav + auth) ─┐
Phase 4 (backend)  ───┼─► independent; do any time, in parallel with the above
Phase 7 (Learn UI) ───┘
Phase 9 (ship) ──► last
```

### Phase 1 — Commit pending groundwork ✅ (`f8a5636`)
- [x] Fix face-index comment in `cube.types.ts`
- [x] Move `jest`, `jest-expo`, `@types/jest` to `devDependencies`
- [x] Stub `applyR` so `tsc` passes
- [x] Commit store, parser, move types, `rotateFaceMatrix`, test, roadmap
- [ ] Merge `cube-engine-groundwork` into `master`

### Phase 2 — Cube engine + parser **[review closely]** (test-first: tests from the chat skeleton land before the engine)
_Builds on:_ move types + parser (`move.types.ts`, `moveParser.ts`), cube store, Jest setup. _See §3.1, §3.2._
- [ ] Write the identity tests first (they fail until the engine exists):
  - [ ] each move then its inverse = solved; any move ×4 = solved
  - [ ] `(R U R' U')` ×6 = solved
  - [ ] every solution in `shared/data/raw/*.json` solves its own `setup` (934 cases)
- [ ] Sticker model: `Sticker { pos, normal, color }`, `createSolvedCube()`, `isSolved()`
- [ ] Integer 90° rotation matrices for x / y / z axes
- [ ] Move table: base → `{ axis, layers, direction }` for `R L U D F B`, `M E S`, `x y z`, and wide `r l u d f b`
- [ ] `applyMove(state, move)` and `applyAlgorithm(state, moves)`
- [ ] Parser: accept wide moves (lowercase + `Rw`), normalize `2'` → `2`, ignore parentheses
- [ ] Connect to the renderer: sticker state → what `generateCubies` needs (or rewrite `generateCubies` to read stickers directly); delete `rotateFaceMatrix` / `applyR` if unused
- [ ] Facelet-string export (54 chars, URFDLB order), needed later for kociemba / scans
- [ ] Store actions: `applyMove`, `applyAlgorithm`, `reset`, `scramble`

**Done when:** all identity tests + the 934-solution data test pass, and a dev-only button that runs `scramble` visibly changes the 3D cube.

### Phase 3 — App navigation + auth fixes **[review diff]**
_Builds on:_ existing auth store, API client, backend `/refresh` + `/logout`. _See §4.1 #2, #3._
- [ ] Add `app/(tabs)/_layout.tsx` with a Learn / Playground tab bar
- [ ] Logout button that calls `POST /v1/auth/logout` and clears both tokens
- [ ] Store `refresh_token` alongside `access_token` on login / register
- [ ] 401 interceptor: refresh once (single in-flight refresh shared by concurrent requests), retry the request, sign out only if refresh fails
- [ ] `checkToken` on startup: if the access token is expired but the refresh token is valid → refresh instead of logging out
- [ ] Remove `console.log(newToken)` from `signIn`
- [ ] Fix `app/index.tsx` redirect flicker

**Done when:** you can stay logged in past 15 minutes, switch tabs, and log out.

### Phase 4 — Backend hardening **[review diff]**
_Builds on:_ existing models, auth routes, Docker setup. _See §4.1 #4–6, #8 and §4.2._
- [ ] Refresh tokens: store `sha256(token)`, look up by indexed hash (no bcrypt loop); clean up expired/revoked rows
- [ ] Unique constraints: `UserAlgorithm(user_id, algorithm_id)`, `AlgorithmCase(subset, name, subgroup)`
- [ ] Catch `IntegrityError` on register → 400
- [ ] `GET /v1/algs`: `ORDER BY`, optional `?subset=` filter
- [ ] Replace toggle endpoints with `PUT /v1/algs/{id}/favorite` / `/learn` taking `{ "value": bool }` (shared upsert helper); update the frontend service
- [ ] Alembic: remove `create_all` from startup, replace both migrations with one baseline, run `alembic upgrade head` on container start
- [ ] One Python package + one image for backend and worker (two commands); drop the `shared/` bind-mount dependency
- [ ] Convert `requirements.txt` files to UTF-8 and trim unused packages (or move to `uv` + `pyproject.toml`)
- [ ] Settings: CORS origins from env, SQL `echo` off by default, drop deprecated `Field(env=...)`
- [ ] pytest suite: auth flow + algs endpoints against a test DB

**Done when:** `docker compose up` on an empty DB migrates, seeds, and passes pytest.

### Phase 5 — Layer turning **[review closely]** (see the 3D migration plan: rendering + input first, turning after Phase 2)
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
_Builds on:_ **Phase 2** (facelet import/export, `applyAlgorithm`), **Phase 4** (single backend/worker package, Alembic), existing Redis + Celery. _See §5._
- [ ] `Scan` model + migration (`status`, `images`, `result`, `error`, `user_id`)
- [ ] `POST /v1/scans` (upload 6 images → store → enqueue `process_scan(scan_id)` → 202) and `GET /v1/scans/{id}`
- [ ] Image storage (volume or MinIO); size/type limits
- [ ] Celery config: `scans` queue, `acks_late`, prefetch 1, time limits, retries for transient errors only
- [ ] Worker: grid detection → sample stickers → CIELAB classification calibrated on centers → validate (9 of each color, solvable) → `kociemba` solve
- [ ] App: camera capture flow (6 faces with an on-screen guide), status polling
- [ ] Sticker correction screen before solving
- [ ] Load the scanned state into the cube and play the solution
- [ ] Flower in docker-compose

**Done when:** you scan a real scrambled cube, correct at most a couple of stickers, and watch it solve.

### Phase 9 — Ship it **[review diff]**
- [ ] GitHub Actions: `tsc`, `jest`, `expo lint`, `pytest`
- [ ] README: what it is, architecture diagram, demo GIF, how to run locally
- [ ] Deploy: API + Postgres + Redis + worker (e.g. Fly / Railway), web build (Vercel / Netlify)
- [ ] Decide whether `ROADMAP.md` stays public as a design doc

