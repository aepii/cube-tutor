import { RotationState, SetOrbitalControlsEnabled, SetTurnInput, TurnInput } from "@/features/cube/types/gesture.types";

export interface Coordinates {
  x: number;
  y: number;
  z: number;
}

export type FaceIndex = 0 | 1 | 2 | 3 | 4 | 5 | 6;
export type CubeData = FaceIndex[][][];

export interface CubieData {
  key: string;
  position: Coordinates;
  faceColors: Map<FaceIndex, FaceIndex>;
}

export interface CubeProps {
  cubeData: CubeData;
  setOrbitalControlsEnabled: SetOrbitalControlsEnabled;
  rotationState: RotationState;
  turnInput: TurnInput | null;
  setTurnInput: SetTurnInput;
}

export interface CubieProps {
  position: Coordinates;
  faceColors: Map<FaceIndex, FaceIndex>;
  setOrbitalControlsEnabled: SetOrbitalControlsEnabled;
  setTurnInput: SetTurnInput;
}
