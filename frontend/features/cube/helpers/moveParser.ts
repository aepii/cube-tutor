import {
  VALID_BASES,
  VALID_MODIFIERS,
} from "@/features/cube/constants/move.constants";
import { Move, MoveBase, MoveModifier } from "@/features/cube/types/move.types";

// Parses one token such as "R", "U'", "r2", "Rw'", "M2'".
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

  // A half turn has no direction, so "2'" is the same move as "2"
  const modifier = rest === "2'" ? "2" : rest;

  if (!VALID_MODIFIERS.has(modifier)) {
    throw new Error(`Invalid move: "${token}"`);
  }

  return { base: base as MoveBase, modifier: modifier as MoveModifier };
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
