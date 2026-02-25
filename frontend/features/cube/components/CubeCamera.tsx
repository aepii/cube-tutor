import { useThree, useFrame } from "@react-three/fiber";
import { CAMERA_CONSTANTS } from "@/features/cube/constants/camera.constants";
import { ZoomScale } from "@/features/cube/types/gesture.types";

export default function CubeCamera({ zoomScale }: { zoomScale: ZoomScale }) {
  const { camera } = useThree();

  useFrame(() => {
    const [x, y, z] = CAMERA_CONSTANTS.DEFAULT_POSITION;
    camera.position.set(x * zoomScale.value, y * zoomScale.value, z * zoomScale.value);
    camera.updateProjectionMatrix();
  });

  return null;
}
