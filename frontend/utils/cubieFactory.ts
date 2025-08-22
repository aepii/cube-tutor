import { CubeData, CubieData, Coordinates, FaceIndex } from "@/types";
import { getCubeCoordinateBounds, getFaceIndices } from "@/utils/cubeHelpers";

export function generateCubies(cubeData: CubeData): CubieData[] {
  const size = cubeData[0].length;
  const [minCoord] = getCubeCoordinateBounds(size);
  const cubies: CubieData[] = [];

  for (let x = 0; x < size; x++) {
    for (let y = 0; y < size; y++) {
      for (let z = 0; z < size; z++) {
        const position: Coordinates = {
          x: minCoord + x,
          y: minCoord + y,
          z: minCoord + z,
        };

        const faceIndices = getFaceIndices(position, size);
        const faceColors = new Map<FaceIndex, FaceIndex>();

        for (const faceIndex of faceIndices) {
          const color = extractFaceColor(cubeData, faceIndex, x, y, z, size);

          faceColors.set(faceIndex, color);
        }

        cubies.push({
          key: `${position.x},${position.y},${position.z}`,
          position,
          faceColors,
        });
      }
    }
  }

  return cubies;
}

function extractFaceColor(
  cubeData: CubeData,
  faceIndex: FaceIndex,
  x: number,
  y: number,
  z: number,
  size: number
): FaceIndex {
  return cubeData[faceIndex][
    faceIndex === 2 || faceIndex === 3 ? x : size - 1 - y
  ][faceIndex === 0 || faceIndex === 1 ? size - 1 - z : z];
}
