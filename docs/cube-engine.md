# Cube engine

Pure TypeScript in [`frontend/features/cube/engine/`](../frontend/features/cube/engine/), with no React or three.js imports. Public API: [`engine/index.ts`](../frontend/features/cube/engine/index.ts).

## Sticker model

The cube is **54 stickers**, each `{ pos, normal, color }` ([`engine/types.ts`](../frontend/features/cube/engine/types.ts)):

| Field | Meaning |
|---|---|
| `pos` | Integer position of the cubie the sticker sits on, each coordinate in {-1, 0, 1} |
| `normal` | Unit axis vector the sticker faces |
| `color` | 0–5, named after the face the color starts on when solved |

- `createSolvedCube()` ([`engine/cube.ts`](../frontend/features/cube/engine/cube.ts)) builds the 54 stickers color by color. A sticker exists wherever `dot(pos, normal) === 1`.
- **A sticker keeps its array index forever.** Moves only change `pos` and `normal`, so two equal states are deep-equal and the tests compare them with `toEqual`.
- No cubie objects and no adjacency tables. The 27 "pieces" exist only in the renderer, which groups stickers by `pos` ([`render/layout.ts`](../frontend/features/cube/render/layout.ts)).

## Coordinates and faces

| Index / color | Face | Axis | Solved color |
|---|---|---|---|
| 0 | R | +X | red |
| 1 | L | −X | orange |
| 2 | U | +Y | white |
| 3 | D | −Y | yellow |
| 4 | F | +Z | green |
| 5 | B | −Z | blue |

- The order R L U D F B matches three.js `BoxGeometry`'s material-group order (+X −X +Y −Y +Z −Z), so a renderer face slot can be used directly as an engine color.
- Moves follow WCA conventions: M follows L, E follows D, S follows F; x, y, z follow R, U, F. Wide moves (`r`, `Rw`) are a face plus the adjacent slice.
- State checks ([`engine/cube.ts`](../frontend/features/cube/engine/cube.ts)): `isSolved`, `isF2LSolved`, `isLastLayerOriented`. All three are independent of how the cube is held. They compare against the current centers and find "up" from the white center.
- Facelet export ([`engine/facelets.ts`](../frontend/features/cube/engine/facelets.ts)): a 54-char string in **U R F D L B** order (the kociemba format). This is a *different* face order from the engine index. It is only used at boundaries (tests today).
- **Open question:** `toFacelets` has no caller outside the tests yet. Its intended consumer (solver or scan import) isn't built.

## How a move is applied

Every move is "rotate these layers of this axis a quarter turn". [`engine/moves.ts`](../frontend/features/cube/engine/moves.ts):

```ts
MOVE_TABLE: Record<MoveBase, { axis, layers, sign }>
  R: { axis: X, layers: [1],        sign: -1 }
  M: { axis: X, layers: [0],        sign: +1 }   // follows L
  r: { axis: X, layers: [0, 1],     sign: -1 }
  x: { axis: X, layers: [-1, 0, 1], sign: -1 }
```

1. `applyMove(state, move)` looks up the spec and calls `applyQuarterTurn` `quarterTurns(move)` times (0–3).
2. `applyQuarterTurn` rotates `pos` and `normal` of every sticker whose coordinate on `axis` is in `layers`, using `rotateQuarter` ([`engine/rotation.ts`](../frontend/features/cube/engine/rotation.ts)). That is an integer 90° rotation by component swaps, with no floats.
3. `sign` is the direction about the +axis (right-hand rule). Faces on the + side (R, U, F) use −1 because "clockwise seen from that face" is −90° about +axis. Faces on the − side use +1.
4. `rotateQuarter` negates with `0 - n`, never `-n`, so it **never produces `-0`**. Jest's `toEqual` tells `0` and `-0` apart.
5. `applyAlgorithm(state, moves)` is a `reduce` over `applyMove`. Every call returns a new state (immutable).

`randomScramble()` ([`engine/scramble.ts`](../frontend/features/cube/engine/scramble.ts)) generates 20 face moves. It never repeats a face back to back and never puts three moves on one axis in a row. The random source can be injected for tests.

## Literal turns vs. state mod 4

A parsed `Move` ([`types/move.types.ts`](../frontend/features/cube/types/move.types.ts), parser in [`helpers/moveParser.ts`](../frontend/features/cube/helpers/moveParser.ts)) is:

```ts
{ base: "R", turns: -2, notation: "R2'" }   // signed quarter turns, exactly as written
```

- **The parser never normalizes.** `R2'` → −2, `R3` → 3, `Rw2'` → base `r`, notation `"Rw2'"`. It rejects `R0` and `R'2`.
- **Only the state reduces mod 4:** `quarterTurns(move) = ((turns % 4) + 4) % 4`. `R3` and `R'` leave the same state.
- **Why:** playback has to animate what was written. `R2'` is a counter-clockwise half turn and `R3` is a 270° clockwise turn, even though they end in the same state as `R2` and `R'`. `literalAngle(move) = turns × sign × 90°` ([`helpers/turnMath.ts`](../frontend/features/cube/helpers/turnMath.ts)) feeds the animation. `notation` is kept for display (the dev overlay shows the move currently playing).

How the store uses this: [`store/useCubeStore.ts`](../frontend/features/cube/store/useCubeStore.ts) queues moves. Each one becomes an `ActiveTurn` that animates through `literalAngle`, and `finishTurn()` then calls `applyMove`. Drag turns go the other way: `moveFor(axis, layer, quarters)` turns a snapped angle back into a single-layer `Move`. See [rendering.md](rendering.md#animations-and-gestures).

## How the tests pin the conventions

| Test | Pins |
|---|---|
| [`tests/engine/moves.test.ts`](../frontend/tests/engine/moves.test.ts) — *move relationships* | `r = R M'`, `l = L M`, `u = U E'`, `d = D E`, `f = F S`, `b = B S'`, `x = R M' L'`, `y = U E' D'`, `z = F S B'`. So M/E/S follow L/D/F and x/y/z follow R/U/F |
| `moves.test.ts` — *direction* | Exact facelet strings after `R` and `U`. Identity tests alone would still pass if every move turned the wrong way |
| `moves.test.ts` — per move | Changes state; move + inverse = identity; ×4 = identity; `2` = two quarters; `'` = three |
| `moves.test.ts` — *move order* | `(R U R' U')`×6 = identity (not earlier); `(R U)` has order 105 |
| [`tests/engine/algorithms.test.ts`](../frontend/tests/engine/algorithms.test.ts) | **Every scraped solution** in `shared/data/raw/*.json` solves its own `setup` (PLL: `isSolved`, OLL: `isLastLayerOriented`, F2L: `isF2LSolved`). A U adjustment ("AUF") is allowed before, and also after for PLL. Every setup must really scramble |
| [`tests/moveParser.test.ts`](../frontend/tests/moveParser.test.ts) | Modifiers kept as written (`R2'` ≠ `R2` in `turns`); state equivalences (`R2'` = `R2`, `R3` = `R'`, `R4` = identity); `quarterTurns` range |
| [`tests/store/turnQueue.test.ts`](../frontend/tests/store/turnQueue.test.ts) | Playback ends in the same state as `applyAlgorithm`; literal angles are kept; drag snapping (<45° snaps back, >45° a quarter, >135° a half) |
| [`tests/engine/scramble.test.ts`](../frontend/tests/engine/scramble.test.ts) | Scramble length, no-repeat and axis rules, deterministic for a given random source |

F2L orientation: the test treats a solution's `orientation` "0"–"3" as the F2L slot (front-right, front-left, back-left, back-right). It moves the case there with a `y` conjugate before checking.
