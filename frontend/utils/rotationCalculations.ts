import { GESTURE_CONSTANTS } from "@/constants";

export function calculateRotationDelta(
  translationX: number,
  translationY: number,
  prevX: number,
  prevY: number,
  sensitivity: number = GESTURE_CONSTANTS.DEFAULT_SENSITIVITY
): { dx: number; dy: number } {
  return {
    dx:
      (translationX - prevX) *
      GESTURE_CONSTANTS.DEFAULT_ROTATION_SPEED *
      sensitivity,
    dy:
      (translationY - prevY) *
      GESTURE_CONSTANTS.DEFAULT_ROTATION_SPEED *
      sensitivity,
  };
}
