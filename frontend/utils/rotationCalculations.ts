import { GESTURE_CONSTANTS } from "@/constants";

export function calculateRotationDelta(
  translationX: number,
  translationY: number,
  translationZ: number,
  prevX: number,
  prevY: number,
  prevZ: number,
  sensitivity: number = GESTURE_CONSTANTS.DEFAULT_SENSITIVITY
): { dx: number; dy: number; dz: number } {
  return {
    dx:
      (translationX - prevX) *
      GESTURE_CONSTANTS.DEFAULT_ROTATION_SPEED *
      sensitivity,
    dy:
      (translationY - prevY) *
      GESTURE_CONSTANTS.DEFAULT_ROTATION_SPEED *
      sensitivity,
    dz:
      (translationZ - prevZ) *
      GESTURE_CONSTANTS.DEFAULT_ROTATION_SPEED *
      sensitivity * GESTURE_CONSTANTS.DEFAULT_Z_MULTIPLIER,
  };
}
