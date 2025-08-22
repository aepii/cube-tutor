import { FaceIndex } from "@/types";

export function faceIndexToFaceColor(faceIndex: FaceIndex): string {
  const colorMap: Record<FaceIndex, string> = {
    0: "#ff0000", // Red
    1: "#ff8000", // Orange
    2: "#ffff00", // Yellow
    3: "#ffffff", // White
    4: "#00ff00", // Green
    5: "#0000ff", // Blue
    6: "#808080", // Gray (default)
  };

  return colorMap[faceIndex];
}
