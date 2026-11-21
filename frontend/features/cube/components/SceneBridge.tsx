import { RefObject, useEffect, useLayoutEffect } from "react";
import { Platform } from "react-native";
import { useThree } from "@/features/cube/three/fiber";
import { SceneHandles } from "@/features/cube/types/input.types";
import { clampZoom } from "@/features/cube/hooks/useCubeInput";
import { INPUT_CONSTANTS } from "@/features/cube/constants/input.constants";

interface SceneBridgeProps {
  sceneRef: RefObject<SceneHandles | null>;
  zoomRef: RefObject<number>;
}

// Lives inside the Canvas and hands the camera, view size and invalidate()
// to gesture callbacks, which run outside the Canvas and need them to raycast.
// Also wires the mouse wheel to zoom on web.
export default function SceneBridge({ sceneRef, zoomRef }: SceneBridgeProps) {
  const camera = useThree((s) => s.camera);
  const size = useThree((s) => s.size);
  const gl = useThree((s) => s.gl);
  const invalidate = useThree((s) => s.invalidate);

  useLayoutEffect(() => {
    sceneRef.current = { camera, size, invalidate };
  }, [sceneRef, camera, size, invalidate]);

  useEffect(() => {
    if (Platform.OS !== "web") return;
    const canvas = gl.domElement;
    const onWheel = (e: WheelEvent) => {
      e.preventDefault(); // don't scroll the page
      zoomRef.current = clampZoom(
        zoomRef.current * Math.exp(e.deltaY * INPUT_CONSTANTS.WHEEL_ZOOM_PER_PX),
      );
      invalidate();
    };
    canvas.addEventListener("wheel", onWheel, { passive: false });
    return () => canvas.removeEventListener("wheel", onWheel);
  }, [gl, invalidate, zoomRef]);

  return null;
}
