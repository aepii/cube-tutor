import { useMemo } from "react";
import { CubeData } from "@/types";
import { generateCubies } from "@/domain/cube";

export function useCubieGeneration(cubeData: CubeData) {
  return useMemo(() => generateCubies(cubeData), [cubeData]);
}
