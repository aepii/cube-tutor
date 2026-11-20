export type FaceMove = "R" | "L" | "U" | "D" | "F" | "B";
export type SliceMove = "M" | "E" | "S";
export type RotationMove = "x" | "y" | "z";
// Wide moves: a face plus the adjacent middle slice. "Rw" is parsed as "r".
export type WideMove = "r" | "l" | "u" | "d" | "f" | "b";
export type MoveBase = FaceMove | SliceMove | RotationMove | WideMove;

// A move exactly as written. Nothing is normalized: playback and animation
// need the notation's literal amount and direction ("R2'" is a counter-clockwise
// half turn, "R3" is a 270° clockwise turn). Only the cube *state* reduces
// turns modulo 4 (see quarterTurns in engine/moves.ts).
export interface Move {
  base: MoveBase;
  // Signed quarter turns, positive = clockwise as seen from the move's face
  // (WCA direction). R = 1, R' = -1, R2 = 2, R2' = -2, R3 = 3, R3' = -3.
  turns: number;
  // The token as written, without parentheses (e.g. "Rw2'"), for display and
  // highlighting the current move during playback.
  notation: string;
}
