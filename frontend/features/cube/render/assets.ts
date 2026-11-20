import * as THREE from "three";
import { RoundedBoxGeometry } from "three/examples/jsm/geometries/RoundedBoxGeometry.js";
import { Color, COLORS } from "@/features/cube/engine";
import { RENDER_CONSTANTS as R } from "@/features/cube/constants/cube.constants";
import {
  CORE_COLOR,
  HIGHLIGHT_EMISSIVE_INTENSITY,
  STICKER_COLORS,
} from "./palette";

// GPU resources shared by every mesh. Created once at module load and never
// disposed: the cube lives for the whole app session, and sharing means 80
// meshes use 2 geometries and 13 materials instead of allocating per piece.

export const coreGeometry = new RoundedBoxGeometry(
  R.CORE_SIZE,
  R.CORE_SIZE,
  R.CORE_SIZE,
  R.CORE_SEGMENTS,
  R.CORE_RADIUS,
);

// Rounded square in the XY plane, extruded toward +Z with a soft bevel.
// The bevel grows the outline, so the shape is shrunk by it to hit TILE_SIZE.
function createTileGeometry(): THREE.BufferGeometry {
  const size = R.TILE_SIZE - 2 * R.TILE_BEVEL;
  const half = size / 2;
  const r = Math.min(R.TILE_RADIUS, half);

  const shape = new THREE.Shape();
  shape.moveTo(-half + r, -half);
  shape.lineTo(half - r, -half);
  shape.quadraticCurveTo(half, -half, half, -half + r);
  shape.lineTo(half, half - r);
  shape.quadraticCurveTo(half, half, half - r, half);
  shape.lineTo(-half + r, half);
  shape.quadraticCurveTo(-half, half, -half, half - r);
  shape.lineTo(-half, -half + r);
  shape.quadraticCurveTo(-half, -half, -half + r, -half);

  const geometry = new THREE.ExtrudeGeometry(shape, {
    depth: R.TILE_DEPTH,
    bevelEnabled: true,
    bevelThickness: R.TILE_BEVEL,
    bevelSize: R.TILE_BEVEL,
    bevelSegments: R.TILE_BEVEL_SEGMENTS,
    curveSegments: R.TILE_CURVE_SEGMENTS,
  });
  geometry.computeVertexNormals();
  return geometry;
}

export const tileGeometry = createTileGeometry();

export const coreMaterial = new THREE.MeshStandardMaterial({
  color: CORE_COLOR,
  roughness: 0.55,
  metalness: 0,
});

function tileMaterial(color: Color, highlighted: boolean) {
  const base = new THREE.Color(STICKER_COLORS[color]);
  return new THREE.MeshStandardMaterial({
    color: base,
    roughness: 0.32,
    metalness: 0,
    emissive: highlighted ? base : new THREE.Color(0x000000),
    emissiveIntensity: highlighted ? HIGHLIGHT_EMISSIVE_INTENSITY : 0,
  });
}

export const tileMaterials: Record<Color, THREE.MeshStandardMaterial> =
  Object.fromEntries(COLORS.map((c) => [c, tileMaterial(c, false)])) as Record<
    Color,
    THREE.MeshStandardMaterial
  >;

export const highlightedTileMaterials: Record<Color, THREE.MeshStandardMaterial> =
  Object.fromEntries(COLORS.map((c) => [c, tileMaterial(c, true)])) as Record<
    Color,
    THREE.MeshStandardMaterial
  >;
