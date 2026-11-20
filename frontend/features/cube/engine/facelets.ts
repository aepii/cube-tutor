import { centerColor } from "./cube";
import { Color, CubeState, Vec3 } from "./types";

// Facelet string: 54 characters, faces in the order U R F D L B, 9 per face,
// row by row as seen looking straight at that face — the format the kociemba
// solver uses:
//   U: seen from above, Back edge at the top     D: seen from below, Front edge at the top
//   F, R, B, L: seen from outside with U at the top
// Each character names the face whose center has that sticker's color, so the
// string describes the cube relative to how it is currently held.

type FaceName = "U" | "R" | "F" | "D" | "L" | "B";

// For each face: its outward normal and the cubie position at (row, col).
const FACE_LAYOUT: { name: FaceName; normal: Vec3; at: (r: number, c: number) => Vec3 }[] = [
  { name: "U", normal: [0, 1, 0], at: (r, c) => [c - 1, 1, r - 1] },
  { name: "R", normal: [1, 0, 0], at: (r, c) => [1, 1 - r, 1 - c] },
  { name: "F", normal: [0, 0, 1], at: (r, c) => [c - 1, 1 - r, 1] },
  { name: "D", normal: [0, -1, 0], at: (r, c) => [c - 1, -1, 1 - r] },
  { name: "L", normal: [-1, 0, 0], at: (r, c) => [-1, 1 - r, c - 1] },
  { name: "B", normal: [0, 0, -1], at: (r, c) => [1 - c, 1 - r, -1] },
];

const key = (pos: Vec3, normal: Vec3) => `${pos.join(",")}|${normal.join(",")}`;

export function toFacelets(state: CubeState): string {
  // Which face name each color currently belongs to (by center position)
  const nameOfColor = new Map<Color, FaceName>();
  for (const face of FACE_LAYOUT) {
    nameOfColor.set(centerColor(state, face.normal), face.name);
  }

  const colorAt = new Map<string, Color>();
  for (const s of state) colorAt.set(key(s.pos, s.normal), s.color);

  let out = "";
  for (const face of FACE_LAYOUT) {
    for (let r = 0; r < 3; r++) {
      for (let c = 0; c < 3; c++) {
        const color = colorAt.get(key(face.at(r, c), face.normal));
        if (color === undefined) throw new Error("Invalid cube state: missing sticker");
        out += nameOfColor.get(color);
      }
    }
  }
  return out;
}
