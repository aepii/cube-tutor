import { FaceIndex, Coordinates } from "./types";

// Returns the minimum and maximum coordinates for a cube of a given size
export const getCubeCoordinateBounds = (size: number): [number, number] => {
  const minCoord = -(size - 1) / 2;
  const maxCoord = (size - 1) / 2;
  return [minCoord, maxCoord];
};

// Returns the face indices for a given position in the cube
export const getFaceIndices = (pos: Coordinates, size: number): FaceIndex[] => {
  const { x, y, z } = pos;
  const [minCoord, maxCoord] = getCubeCoordinateBounds(size);

  const faceIndices: FaceIndex[] = [];

  if (x === maxCoord) faceIndices.push(0); // right face (red)
  if (x === minCoord) faceIndices.push(1); // left face (orange)
  if (y === maxCoord) faceIndices.push(2); // up face (white)
  if (y === minCoord) faceIndices.push(3); // down face (yellow)
  if (z === maxCoord) faceIndices.push(4); // front face (green)
  if (z === minCoord) faceIndices.push(5); // back face (blue)

  return faceIndices;
};
