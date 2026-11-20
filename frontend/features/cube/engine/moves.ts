import { MODIFIER_QUARTER_TURNS } from "@/features/cube/constants/move.constants";
import { Move, MoveBase } from "@/features/cube/types/move.types";
import { rotateQuarter } from "./rotation";
import { CubeState, MoveSpec } from "./types";

// Every move is "rotate these layers of this axis a quarter turn".
// Face moves turn clockwise as seen from outside that face, so faces on the
// + side of an axis (R, U, F) use sign -1 and faces on the - side (L, D, B) use +1.
// WCA conventions: M follows L, E follows D, S follows F;
// x follows R, y follows U, z follows F. Wide moves = face + adjacent slice.
const X = 0, Y = 1, Z = 2;
const ALL = [-1, 0, 1];

export const MOVE_TABLE: Record<MoveBase, MoveSpec> = {
  R: { axis: X, layers: [1], sign: -1 },
  L: { axis: X, layers: [-1], sign: 1 },
  U: { axis: Y, layers: [1], sign: -1 },
  D: { axis: Y, layers: [-1], sign: 1 },
  F: { axis: Z, layers: [1], sign: -1 },
  B: { axis: Z, layers: [-1], sign: 1 },

  M: { axis: X, layers: [0], sign: 1 },
  E: { axis: Y, layers: [0], sign: 1 },
  S: { axis: Z, layers: [0], sign: -1 },

  x: { axis: X, layers: ALL, sign: -1 },
  y: { axis: Y, layers: ALL, sign: -1 },
  z: { axis: Z, layers: ALL, sign: -1 },

  r: { axis: X, layers: [0, 1], sign: -1 },
  l: { axis: X, layers: [-1, 0], sign: 1 },
  u: { axis: Y, layers: [0, 1], sign: -1 },
  d: { axis: Y, layers: [-1, 0], sign: 1 },
  f: { axis: Z, layers: [0, 1], sign: -1 },
  b: { axis: Z, layers: [-1, 0], sign: 1 },
};

// Applies one quarter turn described by `spec`. Returns a new state;
// each sticker keeps its index.
function applyQuarterTurn(state: CubeState, spec: MoveSpec): CubeState {
  const { axis, layers, sign } = spec;
  return state.map((s) =>
    layers.includes(s.pos[axis])
      ? {
          pos: rotateQuarter(s.pos, axis, sign),
          normal: rotateQuarter(s.normal, axis, sign),
          color: s.color,
        }
      : s,
  );
}

export function applyMove(state: CubeState, move: Move): CubeState {
  const spec = MOVE_TABLE[move.base];
  const turns = MODIFIER_QUARTER_TURNS[move.modifier];
  let next = state;
  for (let i = 0; i < turns; i++) {
    next = applyQuarterTurn(next, spec);
  }
  return next;
}

export function applyAlgorithm(state: CubeState, moves: readonly Move[]): CubeState {
  return moves.reduce(applyMove, state);
}
