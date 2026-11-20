export type FaceMove = "R" | "L" | "U" | "D" | "F" | "B";
export type SliceMove = "M" | "E" | "S";
export type RotationMove = "x" | "y" | "z";
// Wide moves: a face plus the adjacent middle slice. "Rw" is parsed as "r".
export type WideMove = "r" | "l" | "u" | "d" | "f" | "b";
export type MoveBase = FaceMove | SliceMove | RotationMove | WideMove;
// "2'" is accepted by the parser but normalized to "2" (a half turn has no direction).
export type MoveModifier = "" | "'" | "2" | "3";

export interface Move {
  base: MoveBase;
  modifier: MoveModifier;
}
