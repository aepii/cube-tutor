import { SharedValue } from "react-native-reanimated";

export interface RotationState {
  xRotation: SharedValue<number>;
  yRotation: SharedValue<number>;
  zRotation: SharedValue<number>;
}

export type ZoomScale = SharedValue<number>;

export interface GestureConfig {
  enabled: boolean;
  sensitivity?: number;
}
