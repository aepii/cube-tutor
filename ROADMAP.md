# CubeTutor — Roadmap

_Last audited 2026-11-14 against the actual code. Supersedes the 2026-08-04 version. Verified state at audit time: `npx tsc --noEmit` fails (1 error, empty `applyR`), `npx jest` passes (1 test)._

## 1. What this project is

An app that teaches speedcubing algorithms (OLL / PLL / F2L) with an interactive 3D cube.

| Part | Stack | Location | State |
|---|---|---|---|
| App | Expo (React Native + web), `@react-three/fiber`, Zustand | `frontend/` | Auth + algorithm list work. 3D cube renders and free-rotates. **Layer turning is 0% wired.** No tab bar. |
| API | FastAPI + SQLModel + Alembic + Postgres | `backend/` | Auth (register/login/refresh/logout) and favorite/learn endpoints work. Refresh-token storage needs rework (§4). `images.py` is a placeholder. |
| Worker | Celery + Redis | `worker/`, `shared/` | Skeleton: one fake `process_image` task that sleeps 3s. |
| Scraper | requests + BeautifulSoup → speedcubedb.com | `scraper/` | Done. Produced `shared/data/raw/*.json`: F2L 41 cases / 622 solutions, OLL 57 / 228, PLL 21 / 84. |

---

## 2. Uncommitted work in the tree (from ~Feb–Mar 2026)

Last commit is 2026-02-26. Everything below was written after it and never committed:

| File | Status | What it is |
|---|---|---|
| `frontend/package.json` / lockfile | modified | Added Jest: `test` / `test:watch` scripts, `jest-expo` preset, `jest`, `jest-expo`, `@types/jest` (these belong in `devDependencies`). |
| `features/cube/types/cube.types.ts` | modified | Split `CubeData` into `FaceData[]`; added a face-index comment block (**the comment is wrong**, see §4.1 #7). |
| `features/cube/helpers/geometry.ts` | modified | Swapped colors so index 2 = White, 3 = Yellow (White on top — correct); gray darkened. |
| `features/cube/components/CubeViewer.tsx` | modified | Reads `cubeData` from `useCubeStore` instead of the hardcoded `DEFAULT_CUBE_DATA`. |
| `features/cube/store/useCubeStore.ts` | new | Zustand store holding `cubeData` + `setCubeData`. |
| `features/cube/types/move.types.ts`, `constants/move.constants.ts` | new | Move notation types (`R L U D F B M E S x y z` + modifiers). |
| `features/cube/helpers/moveParser.ts` | new | `parseMove` / `parseAlgorithm` — tokenizes notation strings. Missing wide moves (§4.1 #1). |
| `features/cube/helpers/cubeState.ts` | new | `rotateFaceMatrix` (works, tested) + empty `applyR` (breaks `tsc`). |
| `frontend/tests/cubeState.test.ts` | new | One test for `rotateFaceMatrix`. |
| `ROADMAP.md` | new | This file. |

**Action:** fix the face-index comment, move Jest packages to `devDependencies`, stub `applyR` so `tsc` passes (or delete it if adopting the sticker model in §3), then commit.

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
7. **Face-index comment is wrong.** `cube.types.ts` says 2 = Yellow (Down), 3 = White (Top). Actual code: index = three.js `BoxGeometry` face slot = `+X, -X, +Y, -Y, +Z, -Z` = **R, L, U, D, F, B**, and `geometry.ts` colors 2 = White (Up), 3 = Yellow (Down). Every move table depends on this — fix it before writing any.
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

## 6. Recommended order

Legend: **[you]** = hand-write it (core logic, interview material); **[delegate]** = let Claude Code do it, then review the diff.

1. **Commit the pending work** (§2): fix face-index comment, move Jest to devDeps, make `tsc` pass. **[delegate]**
2. **Cube engine + parser** (§3.1, §3.2, §4.1 #1): sticker model, `applyMove` / `applyAlgorithm`, wide moves in the parser, identity tests + the 934-solution data test. **[you]**, with Claude reviewing.
3. **App navigation + auth fixes** (§4.1 #2, #3): `(tabs)/_layout.tsx`, logout button calling `/v1/auth/logout`, store both tokens, refresh-and-retry-once on 401 with a single in-flight refresh. **[delegate]**
4. **Backend hardening** (§4.1 #4–6, #8; §4.2): SHA-256 refresh tokens, unique constraints, `ORDER BY` + subset filter, Alembic baseline, unified backend/worker image, UTF-8 + trimmed requirements, idempotent `PUT` endpoints. **[delegate]**, review carefully.
5. **Layer turning** (§3.3, §3.4): single gesture with start-raycast, screen→cube-space direction, pivot-group animation (~150–200 ms), `isTurning` lock, commit to store. **[you]** — this was the blocker last time.
6. **Learn ↔ Playground integration**: tap an algorithm → apply its `setup` → play the solution move by move; scramble / reset / undo in the store. **[split]**
7. **Learn tab polish**: TanStack Query, `SectionList` grouped by subset, active tab styling, loading/retry, filter by favorited/learned, cube thumbnails per case. **[delegate]**
8. **Scan pipeline** (§5): design the worker + CV yourself **[you]**; API endpoints, model, migration, Celery config **[delegate]**.
9. **Ship it**: GitHub Actions (tsc, jest, lint, pytest), backend tests (auth + algs with a test DB), README with architecture diagram + demo GIF, deploy (e.g. API on Fly/Railway, web build on Vercel/Netlify). **[delegate]** — the README/GIF matters a lot for a resume project.
