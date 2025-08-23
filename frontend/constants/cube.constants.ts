import { CubeData, FaceIndex } from "@/types";

export const CUBE_SIZE = 3;

export const CUBE_CONSTANTS = {
  CUBIE_SIZE: 0.95,
  HOVER_BRIGHTNESS_MULTIPLIER: 1.5,
  DEFAULT_FACE_COLOR_INDEX: 6 as FaceIndex,
} as const;

export const GEOMETRY_CONSTANTS = {
  VERTICES_PER_FACE: 6,
  TOTAL_VERTICES: 36,
  COLOR_COMPONENTS_PER_VERTEX: 3,
} as const;

export const DEFAULT_CUBE_DATA: CubeData = [
  Array(CUBE_SIZE).fill(null).map(() => Array(CUBE_SIZE).fill(0)), 
  Array(CUBE_SIZE).fill(null).map(() => Array(CUBE_SIZE).fill(1)), 
  Array(CUBE_SIZE).fill(null).map(() => Array(CUBE_SIZE).fill(2)), 
  Array(CUBE_SIZE).fill(null).map(() => Array(CUBE_SIZE).fill(3)), 
  Array(CUBE_SIZE).fill(null).map(() => Array(CUBE_SIZE).fill(4)), 
  Array(CUBE_SIZE).fill(null).map(() => Array(CUBE_SIZE).fill(5)),
];