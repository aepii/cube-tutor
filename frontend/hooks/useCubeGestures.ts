import { useState } from "react";
import { Gesture } from "react-native-gesture-handler";
import { useSharedValue } from "react-native-reanimated";
import { calculateRotationDelta } from "@/utils";
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
    .onBegin(() => {
      prevXRotation.value = GESTURE_CONSTANTS.INITIAL_POSITION.x;
      prevYRotation.value = GESTURE_CONSTANTS.INITIAL_POSITION.y;
    })
    .onUpdate(({ translationX, translationY }) => {
      if (!orbitalControlsEnabled) return;
      const { dx, dy } = calculateRotationDelta(
        translationX,
        translationY,
        GESTURE_CONSTANTS.INITIAL_POSITION.z,
        prevXRotation.value,
        prevYRotation.value,
        GESTURE_CONSTANTS.INITIAL_POSITION.z
      );

      xRotation.value += dy;
      yRotation.value += dx;

      prevXRotation.value = translationX;
      prevYRotation.value = translationY;
    });

  const zoomGesture = Gesture.Pinch()
    .runOnJS(true)
    .onBegin(() => {
      prevScale.value = scale.value;
    })
    .onUpdate((e) => {
      scale.value = prevScale.value * e.scale;
    });

  const rotationGesture = Gesture.Rotation()
    .runOnJS(true)
    .onBegin(() => {
      prevZRotation.value = GESTURE_CONSTANTS.INITIAL_POSITION.z;
    })
    .onUpdate((e) => {
      if (!orbitalControlsEnabled) return;
      const { dz } = calculateRotationDelta(
        GESTURE_CONSTANTS.INITIAL_POSITION.x,
        GESTURE_CONSTANTS.INITIAL_POSITION.y,
        e.rotation,
        GESTURE_CONSTANTS.INITIAL_POSITION.x,
        GESTURE_CONSTANTS.INITIAL_POSITION.y,
        prevZRotation.value
      );

      zRotation.value += dz;

      prevZRotation.value = e.rotation;
    });

  const composedGestures = Gesture.Race(
    Gesture.Simultaneous(panGesture, zoomGesture),
    rotationGesture
  );

  return {
    orbitalControlsEnabled,
    setOrbitalControlsEnabled,
    rotationState: { xRotation, yRotation, zRotation },
    scale,
    composedGestures,
  };
}
