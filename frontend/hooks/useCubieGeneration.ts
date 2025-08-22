import { useMemo } from "react";
import { CubeData } from "@/types";
import { generateCubies } from "@/utils";

export function useCubieGeneration(cubeData: CubeData) {
  return useMemo(() => generateCubies(cubeData), [cubeData]);
}
