import { MoveBase } from "@/features/cube/types/move.types";

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

// Modifier after the base: optional turn count, optional prime.
// "", "'", "2", "2'", "3", "3'", ... Counts are kept as written, not normalized.
export const MODIFIER_PATTERN = /^(\d*)(')?$/;
