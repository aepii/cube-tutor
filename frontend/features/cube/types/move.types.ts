export type FaceMove = "R" | "L" | "U" | "D" | "F" | "B";
export type SliceMove = "M" | "E" | "S";
export type RotationMove = "x" | "y" | "z";
export type MoveBase = FaceMove | SliceMove | RotationMove;
export type MoveModifier = "" | "'" | "2" | "2'" | "3";

export interface Move {
  base: MoveBase;
  modifier: MoveModifier;
}
