import { MoveBase, MoveModifier } from "@/features/cube/types/move.types";

// Number of clockwise quarter turns each modifier stands for.
export const MODIFIER_QUARTER_TURNS: Record<MoveModifier, number> = {
  "": 1,
  "'": 3,
  "2": 2,
  "3": 3,
};

export const VALID_MODIFIERS: ReadonlySet<string> = new Set<MoveModifier>([
  "",
  "'",
  "2",
  "3",
]);

export const VALID_BASES: ReadonlySet<string> = new Set<MoveBase>([
  "R",
  "L",
  "U",
  "D",
  "F",
  "B",
  "M",
  "E",
  "S",
  "x",
  "y",
  "z",
  "r",
  "l",
  "u",
  "d",
  "f",
  "b",
]);
