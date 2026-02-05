import { CubeData, CubieData, Coordinates, FaceIndex } from "@/types";

export function getCubeCoordinateBounds(size: number): [number, number] {
  const half = Math.floor(size / 2);
  return [-half, half];
}

export function getFaceIndices(
  pos: Coordinates,
  cubeSize: number,
): FaceIndex[] {
  const { x, y, z } = pos;
  const half = Math.floor(cubeSize / 2);
  const faceIndices: FaceIndex[] = [];

  if (z === -half) faceIndices.push(5);
  if (z === half) faceIndices.push(4);
  if (y === -half) faceIndices.push(3);
  if (y === half) faceIndices.push(2);
  if (x === -half) faceIndices.push(1);
  if (x === half) faceIndices.push(0);

  return faceIndices;
}

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
  size: number,
): FaceIndex {
  return cubeData[faceIndex][
    faceIndex === 2 || faceIndex === 3 ? x : size - 1 - y
  ][faceIndex === 0 || faceIndex === 1 ? size - 1 - z : z];
}
