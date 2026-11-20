import { StyleSheet } from "react-native";
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
import DevCubeControls from "./DevCubeControls";

export default function CubeViewer() {
  const { setOrbitalControlsEnabled, rotationState, zoomScale, composedGestures } =
    useCubeGestures();

  const cube = useCubeStore((state) => state.cube);

  return (
    <GestureHandlerRootView style={styles.root}>
      <GestureDetector gesture={composedGestures}>
        <Canvas
          // Render only when something changes (gestures call invalidate()),
          // so the GPU idles when the cube is still. Saves battery on mobile.
          frameloop="demand"
          dpr={[1, 2]}
          gl={{ antialias: true }}
          // No tone mapping, so sticker colors render as defined in the palette
          flat
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
            cube={cube}
            setOrbitalControlsEnabled={setOrbitalControlsEnabled}
            rotationState={rotationState}
          />
        </Canvas>
      </GestureDetector>
      {__DEV__ && <DevCubeControls />}
    </GestureHandlerRootView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
});
