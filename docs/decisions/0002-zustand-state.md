# 0002 — Zustand for client state

**Status:** in effect · **Evidence:** commit `915c94a` (2026-02-25) "Refactored authentication handling to use Zustand for state management and removed AuthProvider". Two stores today: [`useAuthStore`](../../frontend/features/auth/store/useAuthStore.ts) and [`useCubeStore`](../../frontend/features/cube/store/useCubeStore.ts). **No rationale is written down anywhere; the "why" below is inferred from how the code uses the stores.**

## Context
Auth was originally a React Context (`AuthProvider`). Two kinds of code now need state **outside React components**:
- the axios interceptors in [`shared/api/client.ts`](../../frontend/shared/api/client.ts) (read the token, sign out on 401)
- the cube's per-frame and gesture code (`useFrame` in `CubeModel`, gesture-handler callbacks in `useCubeInput`)

## Decision
Small, feature-scoped Zustand stores (`create(...)`). Components subscribe with selectors (`useCubeStore((s) => s.cube)`). Non-React code calls `useCubeStore.getState()` / `useAuthStore.getState()` directly.

High-frequency values deliberately stay *out* of the store. The live drag angle is a module-level `turnAngle = { current }` and zoom is a ref, so a drag doesn't trigger 60 re-renders a second.

## Alternatives
- Keep React Context. *Inferred:* the interceptors can't call hooks, and every context update re-renders all consumers.
- Redux Toolkit. *Inferred:* more ceremony for two small stores. Not mentioned in the repo.
- Plain refs/module state for everything. That is used, but only for the per-frame values.

## Consequences
- \+ `getState()` works from interceptors, `useFrame` and gesture callbacks without prop drilling.
- \+ Selector subscriptions keep re-renders narrow: `CubeModel` re-renders on `cube`, `activeTurn` and `highlight` only.
- \+ Store logic can be tested without rendering ([`tests/store/turnQueue.test.ts`](../../frontend/tests/store/turnQueue.test.ts)).
- − Module-level singletons. Tests have to reset the store state, and `turnAngle` and `nextTurnId` live outside the store, so they aren't reset with it.
- − The two-tier state (store vs. `turnAngle`/refs) has to be understood before you change the animation code.
