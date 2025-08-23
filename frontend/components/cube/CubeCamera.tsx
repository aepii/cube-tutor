import { useThree, useFrame } from "@react-three/fiber";
import { CAMERA_CONSTANTS } from "@/constants";
import { ZoomScale } from "@/types";

export default function CubeCamera({ scale }: { scale: ZoomScale }) {
  const { camera } = useThree();

  useFrame(() => {
    const [x, y, z] = CAMERA_CONSTANTS.DEFAULT_POSITION;
    camera.position.set(x * scale.value, y * scale.value, z * scale.value);
    camera.updateProjectionMatrix();
  });

  return null;
}
