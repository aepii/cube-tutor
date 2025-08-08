import { Canvas } from "@react-three/fiber";
import { DEFAULT_CUBE_DATA } from "@/cube/constants";
import Cube from "./Cube";
import { colors } from "@/theme/colors";
import { OrbitControls } from '@react-three/drei/native'

export default function CubeViewer() {
  return (
    <Canvas style={{ backgroundColor: colors.primary }}>
      <Cube cubeData={DEFAULT_CUBE_DATA} />
      <ambientLight />
      <OrbitControls />
    </Canvas>
  );
}
