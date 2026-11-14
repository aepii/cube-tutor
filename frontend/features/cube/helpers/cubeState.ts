import { FaceData, CubeData } from "@/features/cube/types/cube.types";

export function rotateFaceMatrix(
  face: FaceData,
  direction: "CW" | "CCW",
): FaceData {
  const n = face.length;
  const rotated: FaceData = Array.from({ length: n }, () => Array(n).fill(0));

  for (let i = 0; i < n; i++) {
    for (let j = 0; j < n; j++) {
      if (direction === "CW") {
        rotated[i][j] = face[n - j - 1][i];
      } else {
        rotated[i][j] = face[j][n - i - 1];
      }
    }
  }

  return rotated;
}

// TODO: replace with sticker-model engine (see ROADMAP.md §3.1)
export function applyR(_cubeData: CubeData): CubeData {
  throw new Error("applyR not implemented");
}
