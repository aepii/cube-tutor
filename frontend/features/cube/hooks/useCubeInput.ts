import { RefObject, useRef } from "react";
import * as THREE from "three";
import {
  useCompetingGestures,
  useHoverGesture,
  usePanGesture,
  usePinchGesture,
  useRotationGesture,
  useSimultaneousGestures,
} from "react-native-gesture-handler";
import { dragToLocal, pick } from "@/features/cube/helpers/screenDrag";
import { dragAngle, resolveTurn } from "@/features/cube/helpers/turnMath";
import { isBusy, turnAngle, useCubeStore } from "@/features/cube/store/useCubeStore";
import {
  FaceHit,
  ResolvedTurn,
  SceneHandles,
  ScreenPoint,
} from "@/features/cube/types/input.types";
import { INPUT_CONSTANTS as I } from "@/features/cube/constants/input.constants";

export const clampZoom = (zoom: number) => Math.min(I.ZOOM_MAX, Math.max(I.ZOOM_MIN, zoom));

const WORLD_X = new THREE.Vector3(1, 0, 0);
const WORLD_Y = new THREE.Vector3(0, 1, 0);
const WORLD_Z = new THREE.Vector3(0, 0, 1);
const q = new THREE.Quaternion();

// Rotates the cube about a fixed world axis (screen-aligned, since the camera
// looks down -Z). Premultiplying keeps drags screen-relative however the cube
// is already oriented.
function rotateWorld(group: THREE.Object3D | null, axis: THREE.Vector3, angle: number) {
  if (!group || angle === 0) return;
  group.quaternion.premultiply(q.setFromAxisAngle(axis, angle));
}

interface UseCubeInputArgs {
  sceneRef: RefObject<SceneHandles | null>;
  cubeGroupRef: RefObject<THREE.Group | null>;
  piecesGroupRef: RefObject<THREE.Group | null>;
  zoomRef: RefObject<number>;
}

// One gesture system for web and native (gesture-handler 3 hooks):
// - one finger on a colored face: turn that layer (it follows the finger and
//   snaps to the nearest quarter turn on release)
// - one finger on the background: orbit the cube
// - two fingers: pinch to zoom, twist to roll
// - mouse hover (web): highlight the face under the cursor
// Hit detection is a manual raycast, so R3F pointer events aren't used.
export function useCubeInput({ sceneRef, cubeGroupRef, piecesGroupRef, zoomRef }: UseCubeInputArgs) {
  const drag = useRef<{
    mode: "idle" | "orbit" | "turn";
    hit: FaceHit | null;
    start: ScreenPoint;
    turn: ResolvedTurn | null;
  }>({ mode: "idle", hit: null, start: { x: 0, y: 0 }, turn: null });
  const pinchStartZoom = useRef(1);

  const pickAt = (p: ScreenPoint): FaceHit | null => {
    const scene = sceneRef.current;
    const pieces = piecesGroupRef.current;
    return scene && pieces ? pick(scene.camera, pieces, p, scene.size) : null;
  };

  const pan = usePanGesture({
    maxPointers: 1,
    runOnJS: true,
    onBegin: (e) => {
      const store = useCubeStore.getState();
      const hit = pickAt({ x: e.x, y: e.y });
      const s = drag.current;
      s.start = { x: e.x, y: e.y };
      s.turn = null;
      if (hit && !isBusy(store)) {
        s.mode = "turn";
        s.hit = hit;
        store.setHighlight({ pieceKey: hit.pieceKey, slot: hit.slot });
      } else {
        s.mode = "orbit";
        s.hit = null;
      }
      sceneRef.current?.invalidate();
    },
    onUpdate: (e) => {
      const s = drag.current;
      const scene = sceneRef.current;
      if (!scene) return;

      if (s.mode === "orbit") {
        rotateWorld(cubeGroupRef.current, WORLD_Y, e.changeX * I.ORBIT_RADIANS_PER_PX);
        rotateWorld(cubeGroupRef.current, WORLD_X, e.changeY * I.ORBIT_RADIANS_PER_PX);
        scene.invalidate();
        return;
      }

      if (s.mode !== "turn" || !s.hit || !cubeGroupRef.current) return;
      const local = dragToLocal(scene.camera, cubeGroupRef.current, s.hit, s.start, { x: e.x, y: e.y }, scene.size);
      if (!local) return;

      // Choose the layer once, after the finger has moved far enough to tell
      // the direction; it stays locked for the rest of the gesture.
      if (!s.turn) {
        if (Math.hypot(e.translationX, e.translationY) < I.TURN_START_PX) return;
        const turn = resolveTurn(s.hit.pos, s.hit.normal, local);
        if (!turn) return;
        if (!useCubeStore.getState().startDragTurn(turn.axis, turn.layer)) {
          s.mode = "idle";
          return;
        }
        s.turn = turn;
      }

      turnAngle.current = dragAngle(s.turn, local);
      scene.invalidate();
    },
    onFinalize: () => {
      const s = drag.current;
      const store = useCubeStore.getState();
      if (s.mode === "turn" && s.turn) store.releaseDragTurn();
      store.setHighlight(null);
      s.mode = "idle";
      s.hit = null;
      s.turn = null;
      sceneRef.current?.invalidate();
    },
  });

  const pinch = usePinchGesture({
    runOnJS: true,
    onBegin: () => {
      pinchStartZoom.current = zoomRef.current;
    },
    onUpdate: (e) => {
      zoomRef.current = clampZoom(pinchStartZoom.current / e.scale);
      sceneRef.current?.invalidate();
    },
  });

  const twist = useRotationGesture({
    runOnJS: true,
    onUpdate: (e) => {
      // Screen rotation is clockwise-positive; world Z is counter-clockwise
      rotateWorld(cubeGroupRef.current, WORLD_Z, -e.rotationChange);
      sceneRef.current?.invalidate();
    },
  });

  const hover = useHoverGesture({
    runOnJS: true,
    onUpdate: (e) => {
      if (drag.current.mode !== "idle") return;
      const hit = pickAt({ x: e.x, y: e.y });
      useCubeStore
        .getState()
        .setHighlight(hit ? { pieceKey: hit.pieceKey, slot: hit.slot } : null);
      sceneRef.current?.invalidate();
    },
    onFinalize: () => {
      if (drag.current.mode !== "idle") return;
      useCubeStore.getState().setHighlight(null);
      sceneRef.current?.invalidate();
    },
  });

  const twoFingers = useSimultaneousGestures(pinch, twist);
  const touch = useCompetingGestures(pan, twoFingers);
  return useSimultaneousGestures(touch, hover);
}
