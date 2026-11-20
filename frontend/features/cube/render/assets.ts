import * as THREE from "three";
import { RoundedBoxGeometry } from "three/examples/jsm/geometries/RoundedBoxGeometry.js";
import { Color, COLORS } from "@/features/cube/engine";
import { RENDER_CONSTANTS as R } from "@/features/cube/constants/cube.constants";
import {
  HIGHLIGHT_EMISSIVE_INTENSITY,
  INTERNAL_COLOR,
  STICKER_COLORS,
} from "./palette";

// GPU resources shared by every piece. Created once at module load and never
// disposed: the cube lives for the whole app session, and sharing means 27
// meshes use 1 geometry and 13 materials instead of allocating per piece.

// RoundedBoxGeometry extends BoxGeometry, so it keeps BoxGeometry's 6 material
// groups (+X -X +Y -Y +Z -Z). Each group also covers half of the rounded edges
// next to its face, so a colored face wraps over the edge like real plastic.
export const pieceGeometry = new RoundedBoxGeometry(
  R.PIECE_SIZE,
  R.PIECE_SIZE,
  R.PIECE_SIZE,
  R.PIECE_SEGMENTS,
  R.PIECE_RADIUS,
);

export const internalMaterial = new THREE.MeshStandardMaterial({
  color: INTERNAL_COLOR,
  roughness: 0.6,
  metalness: 0,
});

function faceMaterial(color: Color, highlighted: boolean) {
  const base = new THREE.Color(STICKER_COLORS[color]);
  return new THREE.MeshStandardMaterial({
    color: base,
    roughness: 0.32,
    metalness: 0,
    emissive: highlighted ? base : new THREE.Color(0x000000),
    emissiveIntensity: highlighted ? HIGHLIGHT_EMISSIVE_INTENSITY : 0,
  });
}

const byColor = (highlighted: boolean) =>
  Object.fromEntries(COLORS.map((c) => [c, faceMaterial(c, highlighted)])) as Record<
    Color,
    THREE.MeshStandardMaterial
  >;

export const faceMaterials = byColor(false);
export const highlightedFaceMaterials = byColor(true);
