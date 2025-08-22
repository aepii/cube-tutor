import { RotationState } from "./gesture.types";

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
  setOrbitalControlsEnabled: (enabled: boolean) => void;
  rotationState: RotationState;
}

export interface CubieProps {
  position: Coordinates;
  faceColors: Map<FaceIndex, FaceIndex>;
  setOrbitalControlsEnabled: (enabled: boolean) => void;
}
