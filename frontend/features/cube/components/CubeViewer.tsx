import { useRef } from "react";
import { StyleSheet, View } from "react-native";
import * as THREE from "three";
import {
  GestureDetector,
  GestureHandlerRootView,
} from "react-native-gesture-handler";
import { Canvas } from "@/features/cube/three/fiber";
import { colors } from "@/shared/theme/colors";
import { useCubeInput } from "@/features/cube/hooks/useCubeInput";
import { SceneHandles } from "@/features/cube/types/input.types";
import { GESTURE_ZOOM_DEFAULT } from "@/features/cube/constants/camera.constants";
import Cube from "./Cube";
import CubeCamera from "./CubeCamera";
import CubeLighting from "./CubeLighting";
import DevCubeControls from "./DevCubeControls";
import SceneBridge from "./SceneBridge";

export default function CubeViewer() {
  // Shared between the gesture layer (outside the Canvas) and the scene
  const sceneRef = useRef<SceneHandles | null>(null);
  const cubeGroupRef = useRef<THREE.Group>(null);
  const piecesGroupRef = useRef<THREE.Group>(null);
  const zoomRef = useRef(GESTURE_ZOOM_DEFAULT);

  const gesture = useCubeInput({ sceneRef, cubeGroupRef, piecesGroupRef, zoomRef });

  return (
    <GestureHandlerRootView style={styles.root}>
      <GestureDetector gesture={gesture}>
        {/* Gesture coordinates are relative to this view, which the Canvas fills */}
        <View style={styles.root}>
          <Canvas
            // Render only when something changes (gestures and animations call
            // invalidate()), so the GPU idles when the cube is still.
            frameloop="demand"
            dpr={[1, 2]}
            gl={{ antialias: true }}
            // No tone mapping, so face colors render as defined in the palette
            flat
            style={{
              backgroundColor: colors.primary,
              // Web only: stop the browser from scrolling/zooming the page
              // or selecting text while dragging the cube. Ignored on native.
              touchAction: "none",
              userSelect: "none",
            }}
          >
            <SceneBridge sceneRef={sceneRef} zoomRef={zoomRef} />
            <CubeCamera zoomRef={zoomRef} />
            <CubeLighting />
            <Cube cubeGroupRef={cubeGroupRef} piecesGroupRef={piecesGroupRef} />
          </Canvas>
        </View>
      </GestureDetector>
      {__DEV__ && <DevCubeControls />}
    </GestureHandlerRootView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
});
