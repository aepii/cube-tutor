import { Canvas } from "@react-three/fiber";
import { DEFAULT_CUBE_DATA } from "@/constants";
import { colors } from "@/theme/colors";
import {
  GestureDetector,
  GestureHandlerRootView,
} from "react-native-gesture-handler";
import { useCubeGestures } from "@/hooks";
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
            cubeData={DEFAULT_CUBE_DATA}
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
