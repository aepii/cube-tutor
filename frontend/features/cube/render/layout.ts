import { Color, CubeState, Vec3 } from "@/features/cube/engine";

// Pure layout math for the renderer (no React, no GPU objects), so it can be
// unit-tested.

// Face slots of a box, in three.js BoxGeometry group order. This is the same
// order as engine colors (0..5 = R L U D F B), which is why a slot index can
// be used directly as a material index.
export const FACE_SLOT_NORMALS: readonly Vec3[] = [
  [1, 0, 0], // 0: +X
  [-1, 0, 0], // 1: -X
  [0, 1, 0], // 2: +Y
  [0, -1, 0], // 3: -Y
  [0, 0, 1], // 4: +Z
  [0, 0, -1], // 5: -Z
];

export function faceSlot(normal: Vec3): number {
  return FACE_SLOT_NORMALS.findIndex(
    (n) => n[0] === normal[0] && n[1] === normal[1] && n[2] === normal[2],
  );
}

export interface PieceView {
  key: string;
  pos: Vec3;
  // Color showing on each face slot; null = internal (inner) face
  faces: (Color | null)[];
}

// All 27 grid positions. The hidden center piece is drawn too (all internal),
// so the seams never show the background through the middle.
export const PIECE_POSITIONS: readonly Vec3[] = (() => {
  const positions: Vec3[] = [];
  for (let x = -1; x <= 1; x++) {
    for (let y = -1; y <= 1; y++) {
      for (let z = -1; z <= 1; z++) positions.push([x, y, z]);
    }
  }
  return positions;
})();

const posKey = (p: Vec3) => `${p[0]},${p[1]},${p[2]}`;

// Groups the engine's 54 stickers into the 27 pieces they belong to.
// A piece's outer faces get their sticker colors; every other face is internal.
export function piecesFromState(cube: CubeState): PieceView[] {
  const byPos = new Map<string, PieceView>(
    PIECE_POSITIONS.map((pos) => [
      posKey(pos),
      { key: posKey(pos), pos, faces: [null, null, null, null, null, null] },
    ]),
  );

  for (const sticker of cube) {
    const piece = byPos.get(posKey(sticker.pos));
    if (!piece) throw new Error(`Sticker at invalid position ${posKey(sticker.pos)}`);
    piece.faces[faceSlot(sticker.normal)] = sticker.color;
  }

  return [...byPos.values()];
}
