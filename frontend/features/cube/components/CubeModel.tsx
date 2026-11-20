import { useMemo, useState } from "react";
import { ThreeEvent } from "@/features/cube/three/fiber";
import { CubeState } from "@/features/cube/engine";
import { SetOrbitalControlsEnabled } from "@/features/cube/types/gesture.types";
import { CUBIE_POSITIONS, tilePlacement } from "@/features/cube/render/layout";
import {
  coreGeometry,
  coreMaterial,
  highlightedTileMaterials,
  tileGeometry,
  tileMaterials,
} from "@/features/cube/render/assets";

interface CubeModelProps {
  cube: CubeState;
  setOrbitalControlsEnabled: SetOrbitalControlsEnabled;
}

// Stickerless speedcube: a dark rounded core per piece plus one rounded colored
// tile per sticker, drawn straight from engine state. Tiles are keyed by sticker
// index (stable across moves), so a move only updates their transforms.
export default function CubeModel({ cube, setOrbitalControlsEnabled }: CubeModelProps) {
  const [highlighted, setHighlighted] = useState<number | null>(null);

  const tiles = useMemo(
    () => cube.map((sticker, index) => ({ index, sticker, ...tilePlacement(sticker) })),
    [cube],
  );

  // Touching the cube blocks orbiting (current behavior; replaced by the
  // unified input layer in a later PR)
  const onPointerDown = (e: ThreeEvent<PointerEvent>, tileIndex?: number) => {
    e.stopPropagation();
    if (tileIndex !== undefined) setHighlighted(tileIndex);
    setOrbitalControlsEnabled(false);
  };
  const onPointerUp = (e: ThreeEvent<PointerEvent>) => {
    e.stopPropagation();
    setHighlighted(null);
    setOrbitalControlsEnabled(true);
  };

  return (
    <group>
      {CUBIE_POSITIONS.map((pos) => (
        <mesh
          key={pos.join(",")}
          geometry={coreGeometry}
          material={coreMaterial}
          position={[pos[0], pos[1], pos[2]]}
          onPointerDown={(e) => onPointerDown(e)}
          onPointerUp={onPointerUp}
        />
      ))}

      {tiles.map(({ index, sticker, position, quaternion }) => (
        <mesh
          key={index}
          geometry={tileGeometry}
          material={
            highlighted === index
              ? highlightedTileMaterials[sticker.color]
              : tileMaterials[sticker.color]
          }
          position={position}
          quaternion={quaternion}
          onPointerDown={(e) => onPointerDown(e, index)}
          onPointerUp={onPointerUp}
          onPointerEnter={(e) => {
            e.stopPropagation();
            setHighlighted(index);
          }}
          onPointerLeave={(e) => {
            e.stopPropagation();
            setHighlighted((current) => (current === index ? null : current));
          }}
        />
      ))}
    </group>
  );
}
