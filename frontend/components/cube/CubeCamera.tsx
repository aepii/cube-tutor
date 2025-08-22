import { useThree } from "@react-three/fiber";
import { useMemo } from "react";
import { CAMERA_CONSTANTS } from "@/constants";

export default function CubeCamera() {
  const { camera } = useThree();

  useMemo(() => {
    camera.position.set(...CAMERA_CONSTANTS.DEFAULT_POSITION);
    camera.updateProjectionMatrix();
  }, [camera]);

  return null;
}
