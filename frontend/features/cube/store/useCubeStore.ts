import { create } from "zustand";
import { CubeData } from "@/features/cube/types/cube.types";
import { DEFAULT_CUBE_DATA } from "@/features/cube/constants/cube.constants";

interface CubeState {
  cubeData: CubeData;
  setCubeData: (cubeData: CubeData) => void;
}

export const useCubeStore = create<CubeState>((set) => ({
  cubeData: DEFAULT_CUBE_DATA,

  setCubeData: (cubeData: CubeData) => {
    set({ cubeData: cubeData });
  },
}));
