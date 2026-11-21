# 0003 — Sticker-model cube engine

**Status:** in effect (PR #5, commit `f21d3f7`) · **Evidence:** rationale stated in [`ROADMAP.md`](../../ROADMAP.md) §3.1 and §3.2. Implementation in [`frontend/features/cube/engine/`](../../frontend/features/cube/engine/). Details in [cube-engine.md](../cube-engine.md).

## Context
The app has to apply any WCA move (faces, slices M/E/S, wide moves, rotations x/y/z) and animate it in 3D. An earlier plan (ROADMAP, 2026-08) proposed six face matrices plus a hand-written table of which sticker strips each move cycles. The previous renderer had its own `CubeData` format with a stubbed `applyR`.

## Decision
Represent the cube as 54 stickers `{ pos, normal, color }` with integer coordinates. A move is `{ axis, layers, sign }` in `MOVE_TABLE`, and applying it is an integer 90° rotation of `pos` and `normal` for every sticker in those layers. Face matrices and the URFDLB facelet string are derived only at boundaries (`toFacelets`).

Stated reasons (ROADMAP §3.1):
- **No adjacency tables at all:** `R` = x/{1}, `M` = x/{0}, `r` = x/{0,1}, `x` = x/{−1,0,1}.
- **It maps directly onto rendering:** the 3D view already works in positions, so a turn animation is "rotate these meshes, then commit the new state".

## Alternatives
- **Face arrays + adjacency tables** (the earlier plan). Rejected in §3.1: every move, slice and wide move needs its own hand-written cycle table, which is error-prone.
- **Cubie model** (8 corners + 12 edges with permutation/orientation, as solvers use). Not discussed in the repo. *Inferred:* it's compact and fast for solving, but slices, rotations and wide moves change center positions, and rendering would need a translation layer.

## Consequences
- \+ The whole move set is 18 table rows. Adding a move type is one row.
- \+ The renderer draws straight from the state (`piecesFromState` groups stickers by `pos`), and raycast normals line up with engine normals.
- \+ Testable with identities instead of hand-derived states (ROADMAP §3.2). All 934 scraped solutions double as tests ([`algorithms.test.ts`](../../frontend/tests/engine/algorithms.test.ts)).
- − 54 objects per state, and each move maps over all of them. Fine for UI. *Inferred:* too slow for search-based solving, which would want a cubie or coordinate representation.
- − Two face orders coexist: engine index R L U D F B and facelet U R F D L B. `facelets.ts` documents the conversion in one place.
- − Equality depends on stickers keeping their index and on never producing `-0`. Both are pinned by tests.
