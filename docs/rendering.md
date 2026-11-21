# Rendering and input

The Playground screen ([`app/(tabs)/playground.tsx`](../frontend/app/%28tabs%29/playground.tsx)) renders [`CubeViewer`](../frontend/features/cube/components/CubeViewer.tsx). Everything below lives in [`frontend/features/cube/`](../frontend/features/cube/).

## R3F setup

```
GestureHandlerRootView
└─ GestureDetector (useCubeInput)
   └─ View
      └─ <Canvas frameloop="demand" flat dpr=[1,2]>
         ├─ SceneBridge   hands camera / size / invalidate to gesture code; web wheel zoom
         ├─ CubeCamera    camera position = DEFAULT_POSITION × zoom
         ├─ CubeLighting  ambient + hemisphere + key/fill directional (fixed in world space)
         └─ Cube          outer group = cube orientation (orbit rotates it)
            └─ CubeModel  27 piece meshes drawn from engine state, plus a pivot group for the turning layer
└─ DevCubeControls (__DEV__ only): play an algorithm, Scramble, Reset
```

- **Drawn from engine state.** [`CubeModel`](../frontend/features/cube/components/CubeModel.tsx) reads `cube` from the store. It groups the 54 stickers into 27 pieces with `piecesFromState` ([`render/layout.ts`](../frontend/features/cube/render/layout.ts)) and renders one `RoundedBoxGeometry` mesh per piece. That includes the hidden center, so seams never show the background.
- **Materials per face slot.** BoxGeometry's group order (+X −X +Y −Y +Z −Z) equals the engine color order, so slot *i* gets `faceMaterials[color]`, or `internalMaterial` for inner faces.
- **Shared GPU resources** ([`render/assets.ts`](../frontend/features/cube/render/assets.ts)): 1 geometry and 13 materials (6 face, 6 highlighted, 1 internal), created once at module load and never disposed.
- `flat` turns off tone mapping, so palette colors ([`render/palette.ts`](../frontend/features/cube/render/palette.ts)) render as defined.
- The initial three-quarter view is set once in `useLayoutEffect` ([`Cube.tsx`](../frontend/features/cube/components/Cube.tsx)), not as a prop, so re-renders never reset the user's orientation.

## Web vs. native fiber

R3F ships separate builds: `@react-three/fiber` for web (DOM canvas) and `@react-three/fiber/native` for iOS/Android, which renders through `expo-gl`.

| File | Re-exports from |
|---|---|
| [`three/fiber.ts`](../frontend/features/cube/three/fiber.ts) | `@react-three/fiber` |
| [`three/fiber.native.ts`](../frontend/features/cube/three/fiber.native.ts) | `@react-three/fiber/native` |

- Code imports `@/features/cube/three/fiber`. Metro picks the `.native.ts` file on iOS/Android.
- Both re-export the same set: `Canvas`, `invalidate`, `useFrame`, `useThree`, `ThreeEvent`.
- [`eslint.config.js`](../frontend/eslint.config.js) uses `no-restricted-imports` to make importing either R3F package directly an error everywhere except `features/cube/three/**`.

## Demand frameloop

`<Canvas frameloop="demand">` renders a frame only when something calls `invalidate()`, so the GPU idles while the cube is still. React prop changes invalidate automatically. Anything that mutates three.js objects directly has to invalidate by hand:

| Who changes the scene | How it invalidates |
|---|---|
| Orbit / twist (mutates `cubeGroup.quaternion`) | `sceneRef.current.invalidate()` in the gesture callback |
| Pinch zoom (mutates `zoomRef`, read by `CubeCamera`'s `useFrame`) | same |
| Web mouse wheel | `invalidate()` in `SceneBridge`'s wheel listener |
| Drag turn (writes `turnAngle.current`, outside React) | `scene.invalidate()` in the pan `onUpdate` |
| Hover highlight | store update re-renders, plus explicit `invalidate()` |
| Animated turn | `CubeModel`'s `useFrame` calls `invalidate()` every frame until `t ≥ 1`, which keeps the loop alive for the animation's duration |

`SceneBridge` exists because the gesture callbacks run **outside** the Canvas and can't use `useThree`. It copies `camera`, `size` and `invalidate` into a ref that the gesture code reads.

## Animations and gestures

**One input system** ([`hooks/useCubeInput.ts`](../frontend/features/cube/hooks/useCubeInput.ts)) uses gesture-handler 3 hooks on both web and native. It doesn't use R3F pointer events. Hit testing is a manual raycast (`pick` in [`helpers/screenDrag.ts`](../frontend/features/cube/helpers/screenDrag.ts)). The raycast's `materialIndex` is the face slot, and inner faces don't count as hits.

| Gesture | Effect |
|---|---|
| 1-finger pan starting on a colored face | Turn that layer. The axis and layer lock once the drag passes `TURN_START_PX`; the layer follows the finger and snaps on release |
| 1-finger pan on the background (or while the cube is busy) | Orbit: premultiply world-axis quaternions, so the drag stays screen-relative |
| 2 fingers | Pinch = zoom (camera distance, clamped); twist = roll about world Z |
| Mouse hover (web) | Highlights the face under the cursor (emissive material) |

Drag-turn pipeline (pure math, unit-tested in [`tests/input/`](../frontend/tests/input/)):

1. `dragToLocal` projects the start and current screen points onto the touched face's plane and converts the difference into cube-local coordinates. That makes turning independent of how the cube is held.
2. `resolveTurn` ([`helpers/turnMath.ts`](../frontend/features/cube/helpers/turnMath.ts)) drops the component along the face normal *n* and takes the strongest remaining axis as direction *u*. The rotation axis is *w = n × u*, and the layer is the touched piece's coordinate on *w*.
3. `dragAngle` gives the live angle (1.2 cube units of drag = one quarter turn). It's written to the module-level `turnAngle.current`, **not** React state, so dragging doesn't re-render 60 times a second.
4. On release, `releaseDragTurn()` snaps to the nearest quarter (`snapQuarters`). It converts that to a `Move` with `moveFor` and switches the turn to `"animate"` from the current angle.

**Animated turns** ([`store/useCubeStore.ts`](../frontend/features/cube/store/useCubeStore.ts)):

- `activeTurn` has two kinds: `"drag"` (angle from `turnAngle`) and `"animate"` (eases from `fromAngle` to `toAngle` with `easeOutCubic` over `durationMs`).
- In `CubeModel`, pieces in the turning layers render inside a pivot `<group key={turn.id}>`. `useFrame` sets the pivot's rotation each frame. The key gives every turn a fresh, unrotated pivot.
- At `t ≥ 1`, `finishTurn()` applies the move to the engine state and starts the next queued move **in one store update**. The pieces re-render at their new positions with identity rotation, so no flicker. Raycast normals stay in cube-local space.
- Duration: 150 ms per quarter. Each additional quarter adds 60% of that, and scramble plays at 2× speed ([`constants/input.constants.ts`](../frontend/features/cube/constants/input.constants.ts)).
- A drag can't start while the cube is busy (a turn is playing or moves are queued). Moves enqueued during a turn wait in `queue`.
