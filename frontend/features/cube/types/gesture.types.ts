import { SharedValue } from "react-native-reanimated";

export type RotationState = SharedValue<{
  x: number;
  y: number;
  z: number;
}>;

export interface TurnInput {
  faceNormal: "x" | "y" | "z";
  rotationAxis: "x" | "y" | "z";
  translation: number;
}

export type ZoomScale = SharedValue<number>;

export interface GestureConfig {
  enabled: boolean;
  sensitivity?: number;
}

export type SetOrbitalControlsEnabled = (enabled: boolean) => void;

export type SetTurnInput = (turnInput: TurnInput) => void;