import { useState } from "react";
import { Gesture } from "react-native-gesture-handler";
import { useSharedValue } from "react-native-reanimated";
import { calculateXYRotationDelta, calculateZRotationDelta } from "@/domain/cube";
import { GESTURE_CONSTANTS } from "@/constants";
import { TurnInput } from "@/types";

export function useCubeGestures() {
  const [orbitalControlsEnabled, setOrbitalControlsEnabled] = useState(true);
  const [turnInput, setTurnInput] = useState<TurnInput | null>(null);

  const rotation = useSharedValue({
    x: GESTURE_CONSTANTS.INITIAL_ROTATION,
    y: GESTURE_CONSTANTS.INITIAL_ROTATION,
    z: GESTURE_CONSTANTS.INITIAL_ROTATION,
  });

  const prevRotation = useSharedValue({
    x: GESTURE_CONSTANTS.INITIAL_POSITION.x,
    y: GESTURE_CONSTANTS.INITIAL_POSITION.y,
    z: GESTURE_CONSTANTS.INITIAL_POSITION.z,
  });

  const zoomScale = useSharedValue(GESTURE_CONSTANTS.INITIAL_ZOOM_SCALE);
  const prevZoomScale = useSharedValue(GESTURE_CONSTANTS.INITIAL_ZOOM_SCALE);

  const panGesture = Gesture.Pan()
    .runOnJS(true)
    .maxPointers(1)
    .onUpdate(({ translationX, translationY }) => {
      if (!orbitalControlsEnabled) return;
      const { dx, dy } = calculateXYRotationDelta(
        translationX,
        translationY,
        prevRotation.value.x,
        prevRotation.value.y
      );

      rotation.value = {
        ...rotation.value,
        x: rotation.value.x + dy,
        y: rotation.value.y + dx,
      };

      prevRotation.value = {
        ...prevRotation.value,
        x: translationX,
        y: translationY,
      };
    })
    .onEnd(() => {
      prevRotation.value = {
        ...prevRotation.value,
        x: GESTURE_CONSTANTS.INITIAL_POSITION.x,
        y: GESTURE_CONSTANTS.INITIAL_POSITION.y,
      };
    });

  const zoomGesture = Gesture.Pinch()
    .runOnJS(true)
    .onUpdate((e) => {
      zoomScale.value = prevZoomScale.value / e.scale;
    })
    .onEnd(() => {
      prevZoomScale.value = zoomScale.value;
    });

  const rotationGesture = Gesture.Rotation()
    .runOnJS(true)
    .onUpdate((e) => {
      if (!orbitalControlsEnabled) return;
      const dz = calculateZRotationDelta(-e.rotation, prevRotation.value.z);

      rotation.value = {
        ...rotation.value,
        z: rotation.value.z + dz,
      };

      prevRotation.value = {
        ...prevRotation.value,
        z: -e.rotation,
      };
    })
    .onEnd(() => {
      prevRotation.value = {
        ...prevRotation.value,
        z: GESTURE_CONSTANTS.INITIAL_POSITION.z,
      };
    });

  const composedGestures = Gesture.Race(
    panGesture,
    rotationGesture,
    zoomGesture
  );

  return {
    orbitalControlsEnabled,
    setOrbitalControlsEnabled,
    rotationState: rotation,
    zoomScale,
    composedGestures,
    turnInput,
    setTurnInput,
  };
}
