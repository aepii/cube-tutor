import { MoveModifier } from "@/features/cube/types/move.types";

export const MODIFIER_META: Record<
  MoveModifier,
  { times: number; ccw: boolean }
> = {
  "": { times: 1, ccw: false },
  "'": { times: 1, ccw: true },
  "2": { times: 2, ccw: false },
  "2'": { times: 2, ccw: true },
  "3": { times: 3, ccw: false },
};

export const VALID_MODIFIERS = new Set(["", "'", "2", "2'", "3"]);

export const VALID_BASES = new Set([
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
]);
