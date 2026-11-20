import { CubeState } from "@/features/cube/engine";
import {
  RotationState,
  SetOrbitalControlsEnabled,
} from "@/features/cube/types/gesture.types";

// Cube colors and face conventions live in the engine (engine/types.ts):
// 0..5 = R L U D F B = +X -X +Y -Y +Z -Z, White on Up, Green on Front.

export interface CubeProps {
  cube: CubeState;
  setOrbitalControlsEnabled: SetOrbitalControlsEnabled;
  rotationState: RotationState;
}
