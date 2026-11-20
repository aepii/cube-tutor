import { Canvas } from "@/features/cube/three/fiber";
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
          // Render only when something changes (gestures call invalidate()),
          // so the GPU idles when the cube is still. Saves battery on mobile.
          frameloop="demand"
          dpr={[1, 2]}
          gl={{ antialias: true }}
          style={{
            backgroundColor: colors.primary,
            // Web only: stop the browser from scrolling/zooming the page
            // or selecting text while dragging the cube. Ignored on native.
            touchAction: "none",
            userSelect: "none",
          }}
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
