import { Canvas } from "@react-three/fiber";
import { useCubeStore } from "@/features/cube/store/useCubeStore";
import { colors } from "@/shared/theme/colors";
import {
  GestureDetector,
  GestureHandlerRootView,
} from "react-native-gesture-handler";
import { useCubeGestures } from "@/features/cube/hooks/useCubeGestures";
import Cube from "./Cube";
import CubeCamera from "./CubeCamera";
import CubeLighting from "./CubeLighting";

export default function CubeViewer() {
  const {
    orbitalControlsEnabled,
    setOrbitalControlsEnabled,
    rotationState,
    zoomScale,
    composedGestures,
    turnInput,
    setTurnInput,
  } = useCubeGestures();

  const { cubeData } = useCubeStore();

  return (
    <GestureHandlerRootView>
      <GestureDetector gesture={composedGestures}>
        <Canvas
          style={{ backgroundColor: colors.primary }}
          onPointerUp={() => setOrbitalControlsEnabled(true)}
        >
          <CubeCamera zoomScale={zoomScale} />
          <CubeLighting />
          <Cube
            cubeData={cubeData}
            setOrbitalControlsEnabled={setOrbitalControlsEnabled}
            rotationState={rotationState}
            turnInput={turnInput}
            setTurnInput={setTurnInput}
          />
        </Canvas>
      </GestureDetector>
    </GestureHandlerRootView>
  );
}
