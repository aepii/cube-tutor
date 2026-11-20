import { useFrame, useThree } from "@/features/cube/three/fiber";
import { CAMERA_CONSTANTS } from "@/features/cube/constants/camera.constants";
import { ZoomScale } from "@/features/cube/types/gesture.types";

export default function CubeCamera({ zoomScale }: { zoomScale: ZoomScale }) {
  const { camera } = useThree();

  // Zoom only moves the camera, so the projection matrix doesn't need
  // recomputing. Runs only on frames requested via invalidate() (demand mode).
  useFrame(() => {
    const [x, y, z] = CAMERA_CONSTANTS.DEFAULT_POSITION;
    camera.position.set(
      x * zoomScale.value,
      y * zoomScale.value,
      z * zoomScale.value,
    );
  });

  return null;
}
