import { RefObject, useMemo, useRef } from "react";
import * as THREE from "three";
import { useFrame, useThree } from "@/features/cube/three/fiber";
import { piecesFromState, PieceView } from "@/features/cube/render/layout";
import {
  faceMaterials,
  highlightedFaceMaterials,
  internalMaterial,
  pieceGeometry,
} from "@/features/cube/render/assets";
import { PieceUserData } from "@/features/cube/helpers/screenDrag";
import { easeOutCubic } from "@/features/cube/helpers/turnMath";
import { turnAngle, useCubeStore } from "@/features/cube/store/useCubeStore";

const AXES = [
  new THREE.Vector3(1, 0, 0),
  new THREE.Vector3(0, 1, 0),
  new THREE.Vector3(0, 0, 1),
];

interface CubeModelProps {
  // The group gestures raycast against (all 27 pieces live under it)
  piecesGroupRef: RefObject<THREE.Group | null>;
}

// Stickerless speedcube: 27 rounded pieces of colored plastic, drawn straight
// from engine state. While a layer turns, its pieces render inside a pivot
// group that the frame loop rotates; when the turn ends, the store applies the
// move and the pieces re-render at their new positions.
export default function CubeModel({ piecesGroupRef }: CubeModelProps) {
  const cube = useCubeStore((s) => s.cube);
  const activeTurn = useCubeStore((s) => s.activeTurn);
  const highlight = useCubeStore((s) => s.highlight);
  const invalidate = useThree((s) => s.invalidate);

  const pieces = useMemo(() => piecesFromState(cube), [cube]);
  const pivotRef = useRef<THREE.Group>(null);
  // Animation clock for the current turn (performance.now() at its first frame)
  const clock = useRef<{ turnId: number; start: number }>({ turnId: 0, start: 0 });

  useFrame(() => {
    const turn = useCubeStore.getState().activeTurn;
    const pivot = pivotRef.current;
    if (!turn || !pivot) return;

    let angle: number;
    if (turn.kind === "drag") {
      angle = turnAngle.current;
    } else {
      if (clock.current.turnId !== turn.id) {
        clock.current = { turnId: turn.id, start: performance.now() };
      }
      const elapsed = performance.now() - clock.current.start;
      const t = turn.durationMs <= 0 ? 1 : Math.min(1, elapsed / turn.durationMs);
      angle = turn.fromAngle + (turn.toAngle - turn.fromAngle) * easeOutCubic(t);

      if (t >= 1) {
        pivot.setRotationFromAxisAngle(AXES[turn.axis], turn.toAngle);
        useCubeStore.getState().finishTurn();
        invalidate();
        return;
      }
      invalidate();
    }
    pivot.setRotationFromAxisAngle(AXES[turn.axis], angle);
  });

  const inTurningLayer = (piece: PieceView) =>
    activeTurn !== null && activeTurn.layers.includes(piece.pos[activeTurn.axis]);

  const renderPiece = (piece: PieceView) => {
    const userData: PieceUserData = {
      pieceKey: piece.key,
      pos: piece.pos,
      colored: piece.faces.map((c) => c !== null),
    };
    const materials = piece.faces.map((color, slot) => {
      if (color === null) return internalMaterial;
      const lit = highlight?.pieceKey === piece.key && highlight.slot === slot;
      return lit ? highlightedFaceMaterials[color] : faceMaterials[color];
    });
    return (
      <mesh
        key={piece.key}
        geometry={pieceGeometry}
        material={materials}
        position={[piece.pos[0], piece.pos[1], piece.pos[2]]}
        userData={userData}
      />
    );
  };

  return (
    <group ref={piecesGroupRef}>
      {pieces.filter((p) => !inTurningLayer(p)).map(renderPiece)}
      {activeTurn && (
        // Keyed per turn so every turn starts from a fresh, unrotated pivot
        <group key={activeTurn.id} ref={pivotRef}>
          {pieces.filter(inTurningLayer).map(renderPiece)}
        </group>
      )}
    </group>
  );
}
