import * as THREE from "three";
import { FaceIndex } from "@/types";
import { CUBE_CONSTANTS, GEOMETRY_CONSTANTS } from "@/constants";
import { faceIndexToFaceColor } from "@/utils/cubeMaps";

export function createCubieGeometry(
  faceColors: Map<FaceIndex, FaceIndex>,
  isHovered: boolean
): THREE.BufferGeometry {
  const boxGeometry = new THREE.BoxGeometry(
    CUBE_CONSTANTS.CUBIE_SIZE,
    CUBE_CONSTANTS.CUBIE_SIZE,
    CUBE_CONSTANTS.CUBIE_SIZE
  ).toNonIndexed();

  const geometryColors = initializeDefaultColors();
  applyFaceColors(geometryColors, faceColors, isHovered);

  boxGeometry.setAttribute(
    "color",
    new THREE.Float32BufferAttribute(
      geometryColors,
      GEOMETRY_CONSTANTS.COLOR_COMPONENTS_PER_VERTEX
    )
  );

  return boxGeometry;
}

function initializeDefaultColors(): number[] {
  const colors: number[] = [];
  const defaultColor = new THREE.Color(
    faceIndexToFaceColor(CUBE_CONSTANTS.DEFAULT_FACE_COLOR_INDEX)
  );

  for (let i = 0; i < GEOMETRY_CONSTANTS.TOTAL_VERTICES; i++) {
    colors.push(defaultColor.r, defaultColor.g, defaultColor.b);
  }

  return colors;
}

function applyFaceColors(
  geometryColors: number[],
  faceColors: Map<FaceIndex, FaceIndex>,
  isHovered: boolean
): void {
  const multiplier = isHovered ? CUBE_CONSTANTS.HOVER_BRIGHTNESS_MULTIPLIER : 1;

  for (const [faceIndex, colorIndex] of faceColors) {
    const color = new THREE.Color(faceIndexToFaceColor(colorIndex));

    const vertexStart = faceIndex * GEOMETRY_CONSTANTS.VERTICES_PER_FACE;

    for (let i = 0; i < GEOMETRY_CONSTANTS.VERTICES_PER_FACE; i++) {
      const offset =
        (vertexStart + i) * GEOMETRY_CONSTANTS.COLOR_COMPONENTS_PER_VERTEX;
      geometryColors[offset] = color.r * multiplier;
      geometryColors[offset + 1] = color.g * multiplier;
      geometryColors[offset + 2] = color.b * multiplier;
    }
  }
}
