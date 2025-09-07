import { useState } from "react";
import { Gesture } from "react-native-gesture-handler";
import { useSharedValue } from "react-native-reanimated";
import { calculateXYRotationDelta, calculateZRotationDelta } from "@/utils";
import { GESTURE_CONSTANTS } from "@/constants";

export function useCubeGestures() {
  const [orbitalControlsEnabled, setOrbitalControlsEnabled] = useState(true);

  const xRotation = useSharedValue(GESTURE_CONSTANTS.INITIAL_ROTATION);
  const yRotation = useSharedValue(GESTURE_CONSTANTS.INITIAL_ROTATION);
  const zRotation = useSharedValue(GESTURE_CONSTANTS.INITIAL_ROTATION);
  const prevXRotation = useSharedValue(GESTURE_CONSTANTS.INITIAL_POSITION.x);
  const prevYRotation = useSharedValue(GESTURE_CONSTANTS.INITIAL_POSITION.y);
  const prevZRotation = useSharedValue(GESTURE_CONSTANTS.INITIAL_POSITION.z);

  const scale = useSharedValue(GESTURE_CONSTANTS.INITIAL_ZOOM_SCALE);
  const prevScale = useSharedValue(GESTURE_CONSTANTS.INITIAL_ZOOM_SCALE);

  const panGesture = Gesture.Pan()
    .runOnJS(true)
    .maxPointers(1)
    .onUpdate(({ translationX, translationY }) => {
      if (!orbitalControlsEnabled) return;
      console.log("PAN");
      const { dx, dy } = calculateXYRotationDelta(
        translationX,
        translationY,
        prevXRotation.value,
        prevYRotation.value
      );

      xRotation.value += dy;
      yRotation.value += dx;

      prevXRotation.value = translationX;
      prevYRotation.value = translationY;
    })
    .onEnd(() => {
      prevXRotation.value = GESTURE_CONSTANTS.INITIAL_POSITION.x;
      prevYRotation.value = GESTURE_CONSTANTS.INITIAL_POSITION.y;
    });

  const zoomGesture = Gesture.Pinch()
    .runOnJS(true)
    .onUpdate((e) => {
      scale.value = prevScale.value / e.scale;
      console.log(scale.value);
    })
    .onEnd(() => {
      prevScale.value = scale.value;
    });

  const rotationGesture = Gesture.Rotation()
    .runOnJS(true)
    .onUpdate((e) => {
      if (!orbitalControlsEnabled) return;
      const dz = calculateZRotationDelta(-e.rotation, prevZRotation.value);

      zRotation.value += dz;

      prevZRotation.value = -e.rotation;
    })
    .onEnd(() => {
      prevZRotation.value = GESTURE_CONSTANTS.INITIAL_POSITION.z;
    });

  const composedGestures = Gesture.Race(
    panGesture,
    rotationGesture,
    zoomGesture
  );

  return {
    orbitalControlsEnabled,
    setOrbitalControlsEnabled,
    rotationState: { xRotation, yRotation, zRotation },
    scale,
    composedGestures,
  };
}
