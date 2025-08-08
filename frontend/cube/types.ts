export type FaceIndex = 0 | 1 | 2 | 3 | 4 | 5 | 6;

export type FaceString =
  | "right"
  | "left"
  | "up"
  | "down"
  | "front"
  | "back"
  | "default";

export type CubeData = number[][][];

export type Coordinates = { x: number; y: number; z: number };
