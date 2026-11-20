import { Color, CubeState, Sticker, Vec3 } from "./types";

// Outward normal of each face in the solved cube, indexed by Color.
export const FACE_NORMALS: Record<Color, Vec3> = {
  0: [1, 0, 0], // R
  1: [-1, 0, 0], // L
  2: [0, 1, 0], // U
  3: [0, -1, 0], // D
  4: [0, 0, 1], // F
  5: [0, 0, -1], // B
};

export const COLORS: readonly Color[] = [0, 1, 2, 3, 4, 5];

// The color that starts on Up; algorithm checks treat it as the last layer.
export const UP_COLOR: Color = 2;

const dot = (a: Vec3, b: Vec3) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const sameVec = (a: Vec3, b: Vec3) => a[0] === b[0] && a[1] === b[1] && a[2] === b[2];

export function createSolvedCube(): CubeState {
  const stickers: Sticker[] = [];
  for (const color of COLORS) {
    const normal = FACE_NORMALS[color];
    for (let x = -1; x <= 1; x++) {
      for (let y = -1; y <= 1; y++) {
        for (let z = -1; z <= 1; z++) {
          const pos: Vec3 = [x, y, z];
          // The sticker sits on the cubies of the outer layer the normal points to
          if (dot(pos, normal) === 1) {
            stickers.push({ pos, normal, color });
          }
        }
      }
    }
  }
  return stickers;
}

// Color of the center sticker currently facing `normal`.
export function centerColor(state: CubeState, normal: Vec3): Color {
  const center = state.find((s) => sameVec(s.pos, normal) && sameVec(s.normal, normal));
  if (!center) throw new Error("Invalid cube state: missing center");
  return center.color;
}

// Solved = every face shows one color. This does not care how the cube is held,
// so whole-cube rotations (x, y, z) keep a solved cube solved.
export function isSolved(state: CubeState): boolean {
  return COLORS.every((face) => {
    const normal = FACE_NORMALS[face];
    const expected = centerColor(state, normal);
    return state.every((s) => !sameVec(s.normal, normal) || s.color === expected);
  });
}

// Direction the Up-colored center currently faces.
function upNormal(state: CubeState): Vec3 {
  const center = state.find(
    (s) => s.color === UP_COLOR && sameVec(s.pos, s.normal),
  );
  if (!center) throw new Error("Invalid cube state: missing center");
  return center.normal;
}

// First two layers solved: every sticker outside the last layer (the layer at the
// Up-colored center) matches the center of the face it points to.
// Independent of how the cube is held.
export function isF2LSolved(state: CubeState): boolean {
  const up = upNormal(state);
  return state.every(
    (s) => dot(s.pos, up) === 1 || s.color === centerColor(state, s.normal),
  );
}

// First two layers solved and the last layer's top face all one color (OLL done).
export function isLastLayerOriented(state: CubeState): boolean {
  const up = upNormal(state);
  return (
    isF2LSolved(state) &&
    state.every((s) => !sameVec(s.normal, up) || s.color === UP_COLOR)
  );
}
