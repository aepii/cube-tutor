import { useMemo, useState } from "react";
import { ThreeEvent } from "@/features/cube/three/fiber";
import { CubeState } from "@/features/cube/engine";
import { SetOrbitalControlsEnabled } from "@/features/cube/types/gesture.types";
import { piecesFromState, PieceView } from "@/features/cube/render/layout";
import {
  faceMaterials,
  highlightedFaceMaterials,
  internalMaterial,
  pieceGeometry,
} from "@/features/cube/render/assets";

interface CubeModelProps {
  cube: CubeState;
  setOrbitalControlsEnabled: SetOrbitalControlsEnabled;
}

// A touched face: which piece, and which of its 6 face slots
interface FaceRef {
  piece: string;
  slot: number;
}

// Stickerless speedcube: 27 rounded pieces of colored plastic, drawn straight
// from engine state. Each piece is one mesh with a material per face slot:
// outer faces use the sticker color, inner faces the internal color.
export default function CubeModel({ cube, setOrbitalControlsEnabled }: CubeModelProps) {
  const [highlighted, setHighlighted] = useState<FaceRef | null>(null);
  const pieces = useMemo(() => piecesFromState(cube), [cube]);

  const materialsFor = (piece: PieceView) =>
    piece.faces.map((color, slot) => {
      if (color === null) return internalMaterial;
      const isHighlighted = highlighted?.piece === piece.key && highlighted.slot === slot;
      return isHighlighted ? highlightedFaceMaterials[color] : faceMaterials[color];
    });

  // The raycast hit's materialIndex is the face slot that was touched.
  // Only colored (outer) faces highlight.
  const touchedFace = (e: ThreeEvent<PointerEvent>, piece: PieceView): FaceRef | null => {
    const slot = e.face?.materialIndex;
    return slot !== undefined && piece.faces[slot] !== null ? { piece: piece.key, slot } : null;
  };

  return (
    <group>
      {pieces.map((piece) => (
        <mesh
          key={piece.key}
          geometry={pieceGeometry}
          material={materialsFor(piece)}
          position={[piece.pos[0], piece.pos[1], piece.pos[2]]}
          // Touching the cube blocks orbiting (current behavior; replaced by
          // the unified input layer in a later PR)
          onPointerDown={(e) => {
            e.stopPropagation();
            setHighlighted(touchedFace(e, piece));
            setOrbitalControlsEnabled(false);
          }}
          onPointerUp={(e) => {
            e.stopPropagation();
            setHighlighted(null);
            setOrbitalControlsEnabled(true);
          }}
          onPointerMove={(e) => {
            e.stopPropagation();
            const face = touchedFace(e, piece);
            setHighlighted((current) =>
              current?.piece === face?.piece && current?.slot === face?.slot ? current : face,
            );
          }}
          onPointerLeave={(e) => {
            e.stopPropagation();
            setHighlighted((current) => (current?.piece === piece.key ? null : current));
          }}
        />
      ))}
    </group>
  );
}
