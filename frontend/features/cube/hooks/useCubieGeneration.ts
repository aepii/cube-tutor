import { useMemo } from "react";
import { CubeData } from "@/features/cube/types/cube.types";
import { generateCubies } from "@/features/cube/helpers/math";

export function useCubieGeneration(cubeData: CubeData) {
  return useMemo(() => generateCubies(cubeData), [cubeData]);
}
