import { useState } from "react";
import { Gesture } from "react-native-gesture-handler";
import { useSharedValue } from "react-native-reanimated";
import { calculateRotationDelta } from "@/utils";
import { GESTURE_CONSTANTS } from "@/constants";

export function useCubeGestures() {
  const [orbitalControlsEnabled, setOrbitalControlsEnabled] = useState(true);
  const xRotation = useSharedValue(GESTURE_CONSTANTS.INITIAL_ROTATION);
  const yRotation = useSharedValue(GESTURE_CONSTANTS.INITIAL_ROTATION);
  const prev = useSharedValue(GESTURE_CONSTANTS.INITIAL_POSITION);

  const panGesture = Gesture.Pan()
    .onBegin(() => {
      prev.value = GESTURE_CONSTANTS.INITIAL_POSITION;
    })
    .onUpdate(({ translationX, translationY }) => {
      if (!orbitalControlsEnabled) return;

      const { dx, dy } = calculateRotationDelta(
        translationX,
        translationY,
        prev.value.x,
        prev.value.y
      );

      xRotation.value += dy;
      yRotation.value += dx;

      prev.value = { x: translationX, y: translationY };
    });

  return {
    orbitalControlsEnabled,
    setOrbitalControlsEnabled,
    rotationState: { xRotation, yRotation },
    panGesture,
  };
}
