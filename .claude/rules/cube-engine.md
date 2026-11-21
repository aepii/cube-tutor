---
paths:
  - "frontend/features/cube/**"
  - "frontend/tests/engine/**"
  - "frontend/tests/moveParser.test.ts"
  - "frontend/tests/store/turnQueue.test.ts"
---

# Cube engine conventions

- **Cube conventions:** face index 0–5 = R L U D F B = +X −X +Y −Y +Z −Z (three.js `BoxGeometry` slot order). White on Up (+Y), Green on Front (+Z), Red on Right (+X). WCA move conventions: M follows L, E follows D, S follows F; x, y, z follow R, U, F. The engine tests pin these; don't change them without updating the tests deliberately.
- **Engine:** 54 stickers `{ pos, normal, color }` with integer coords; every move is a quarter-turn rotation of some layers on one axis (`engine/moves.ts` `MOVE_TABLE`). Stickers keep their array index, so states compare with `toEqual`. Avoid producing `-0`.
- **Moves are never normalized.** A parsed `Move` keeps `turns` (signed quarter turns as written: `R2'` = −2, `R3` = 3) and the original `notation`. Playback/animation must animate the literal amount and direction (`R2'` = counter-clockwise half turn, `R3` = 270° clockwise). Only the cube *state* reduces modulo 4 (`quarterTurns` in `engine/moves.ts`).
