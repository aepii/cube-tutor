import { Quaternion, Vector3 } from "three";
import { Sticker, Vec3 } from "@/features/cube/engine";
import { CORE_HALF } from "@/features/cube/constants/cube.constants";

// Pure placement math for the renderer (no React, no GPU objects), so it can
// be unit-tested.

export type QuaternionTuple = [number, number, number, number];

export interface TilePlacement {
  position: [number, number, number];
  quaternion: QuaternionTuple;
}

// The 26 visible cubie positions (every grid point except the hidden center).
export const CUBIE_POSITIONS: readonly Vec3[] = (() => {
  const positions: Vec3[] = [];
  for (let x = -1; x <= 1; x++) {
    for (let y = -1; y <= 1; y++) {
      for (let z = -1; z <= 1; z++) {
        if (x !== 0 || y !== 0 || z !== 0) positions.push([x, y, z]);
      }
    }
  }
  return positions;
})();

const TILE_FORWARD = new Vector3(0, 0, 1);

// Tile geometry is built facing +Z; rotate it to face the sticker's normal and
// place it on the outer surface of the sticker's cubie core.
export function tilePlacement(sticker: Sticker): TilePlacement {
  const [px, py, pz] = sticker.pos;
  const [nx, ny, nz] = sticker.normal;

  const q = new Quaternion().setFromUnitVectors(
    TILE_FORWARD,
    new Vector3(nx, ny, nz),
  );

  return {
    position: [px + nx * CORE_HALF, py + ny * CORE_HALF, pz + nz * CORE_HALF],
    quaternion: [q.x, q.y, q.z, q.w],
  };
}
