import { create } from "zustand";
import {
  CubeState,
  applyAlgorithm,
  createSolvedCube,
  randomScramble,
} from "@/features/cube/engine";
import { parseAlgorithm } from "@/features/cube/helpers/moveParser";

interface CubeStore {
  // Engine state: 54 stickers. The renderer draws directly from this.
  cube: CubeState;
  // The last scramble applied, for display (null when solved/reset)
  lastScramble: string | null;

  // Applies an algorithm instantly (no animation yet), e.g. "R U R' U'"
  applyAlgorithm: (alg: string) => void;
  // Resets to solved, then applies a random 20-move scramble
  scramble: () => void;
  reset: () => void;
}

export const useCubeStore = create<CubeStore>((set) => ({
  cube: createSolvedCube(),
  lastScramble: null,

  applyAlgorithm: (alg) => {
    set((state) => ({ cube: applyAlgorithm(state.cube, parseAlgorithm(alg)) }));
  },

  scramble: () => {
    const scramble = randomScramble();
    set({
      cube: applyAlgorithm(createSolvedCube(), parseAlgorithm(scramble)),
      lastScramble: scramble,
    });
  },

  reset: () => {
    set({ cube: createSolvedCube(), lastScramble: null });
  },
}));
