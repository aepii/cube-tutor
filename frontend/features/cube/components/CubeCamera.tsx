import { RefObject } from "react";
import { useFrame, useThree } from "@/features/cube/three/fiber";
import { CAMERA_CONSTANTS } from "@/features/cube/constants/camera.constants";

// Places the camera at the default position scaled by the zoom factor.
// Zoom only moves the camera, so the projection matrix doesn't need
// recomputing. Runs only on frames requested via invalidate() (demand mode).
export default function CubeCamera({ zoomRef }: { zoomRef: RefObject<number> }) {
  const { camera } = useThree();

  useFrame(() => {
    const [x, y, z] = CAMERA_CONSTANTS.DEFAULT_POSITION;
    const zoom = zoomRef.current;
    camera.position.set(x * zoom, y * zoom, z * zoom);
  });

  return null;
}
