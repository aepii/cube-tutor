import {
  MODIFIER_PATTERN,
  VALID_BASES,
} from "@/features/cube/constants/move.constants";
import { Move, MoveBase } from "@/features/cube/types/move.types";

// Parses one token such as "R", "U'", "r2", "Rw'", "M2'", "R3".
// The amount and direction are kept exactly as written (no normalization),
// so playback can animate "R2'" as a counter-clockwise half turn.
export function parseMove(token: string): Move {
  let base = token[0];
  let rest = token.slice(1);

  // "Rw" style wide moves are the same as lowercase "r"
  if (rest.startsWith("w") && "RLUDFB".includes(base)) {
    base = base.toLowerCase();
    rest = rest.slice(1);
  }

  if (!VALID_BASES.has(base)) {
    throw new Error(`Invalid move: "${token}"`);
  }

  const match = MODIFIER_PATTERN.exec(rest);
  if (!match) {
    throw new Error(`Invalid move: "${token}"`);
  }

  const count = match[1] === "" ? 1 : Number(match[1]);
  if (count === 0) {
    throw new Error(`Invalid move: "${token}"`);
  }
  const turns = match[2] ? -count : count;

  return { base: base as MoveBase, turns, notation: token };
}

// Parses a whole algorithm string, e.g. "(R U R' U') y r2".
// Parentheses (used for grouping/finger tricks) are ignored.
export function parseAlgorithm(alg: string): Move[] {
  return alg
    .replace(/[()]/g, " ")
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .map(parseMove);
}
