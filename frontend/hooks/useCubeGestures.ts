import { useState } from "react";
import { Gesture } from "react-native-gesture-handler";
import { useSharedValue } from "react-native-reanimated";
import { calculateRotationDelta } from "@/utils";
import { GESTURE_CONSTANTS } from "@/constants";

export function useCubeGestures() {
  const [orbitalControlsEnabled, setOrbitalControlsEnabled] = useState(true);
  const xRotation = useSharedValue(GESTURE_CONSTANTS.INITIAL_ROTATION);
  const yRotation = useSharedValue(GESTURE_CONSTANTS.INITIAL_ROTATION);
  const prevXRotation = useSharedValue(GESTURE_CONSTANTS.INITIAL_POSITION.x);
  const prevYRotation = useSharedValue(GESTURE_CONSTANTS.INITIAL_POSITION.y);

  const panGesture = Gesture.Pan()
    .runOnJS(true)

    .onBegin(() => {
      prevXRotation.value = GESTURE_CONSTANTS.INITIAL_POSITION.x;
      prevYRotation.value = GESTURE_CONSTANTS.INITIAL_POSITION.y;
    })
    .onUpdate(({ translationX, translationY }) => {
      if (!orbitalControlsEnabled) return;
      const { dx, dy } = calculateRotationDelta(
        translationX,
        translationY,
        prevXRotation.value,
        prevYRotation.value
      );

      xRotation.value += dy;
      yRotation.value += dx;

      prevXRotation.value = translationX;
      prevYRotation.value = translationY;
    });

  return {
    orbitalControlsEnabled,
    setOrbitalControlsEnabled,
    rotationState: { xRotation, yRotation },
    panGesture,
  };
}
