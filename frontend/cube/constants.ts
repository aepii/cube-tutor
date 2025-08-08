import { FaceIndex, FaceString, CubeData } from "./types";

export const DEFAULT_CUBE_DATA: CubeData = [
  Array(3).fill(Array(3).fill(0)),
  Array(3).fill(Array(3).fill(1)),
  Array(3).fill(Array(3).fill(2)),
  Array(3).fill(Array(3).fill(3)),
  Array(3).fill(Array(3).fill(4)),
  Array(3).fill(Array(3).fill(5)),
];

export const FACE_MAP: Record<FaceIndex, FaceString> = {
  0: "right",
  1: "left",
  2: "up",
  3: "down",
  4: "front",
  5: "back",
  6: "default",
};

export const FACE_COLOR_MAP: Record<FaceIndex, string> = {
  0: "#ff0000", // red
  1: "#ffa500", // orange
  2: "#ffffff", // white
  3: "#ffff00", // yellow
  4: "#00ff00", // green
  5: "#0000ff", // blue
  6: "#666666", // gray
};
