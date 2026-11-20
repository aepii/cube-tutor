import {
  MODIFIER_META,
  VALID_BASES,
  VALID_MODIFIERS,
} from "@/features/cube/constants/move.constants";

import { Move, MoveBase, MoveModifier } from "@/features/cube/types/move.types";

export function parseMove(token: string): Move {
  const base = token[0] as MoveBase;

  if (!VALID_BASES.has(base)) {
    throw new Error(`Invalid move base: "${base}"`);
  }

  const modifier = token.slice(1) as MoveModifier;

  if (!VALID_MODIFIERS.has(modifier)) {
    throw new Error(`Invalid modifier: "${modifier}"`);
  }

  return { base, modifier };
}

export function parseAlgorithm(alg: string): Move[] {
  const tokens = alg.trim().split(/\s+/).filter(Boolean);
  return tokens.map(parseMove);
}
