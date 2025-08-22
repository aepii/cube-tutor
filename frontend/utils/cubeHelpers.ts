import { FaceIndex, Coordinates } from "@/types";

export function getCubeCoordinateBounds(size: number): [number, number] {
  const half = Math.floor(size / 2);
  return [-half, half];
}

export function getFaceIndices(
  pos: Coordinates,
  cubeSize: number
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
