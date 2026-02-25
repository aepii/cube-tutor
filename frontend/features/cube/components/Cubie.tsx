import { useState, useMemo } from "react";
import { CubieProps } from "@/features/cube/types/cube.types";
import { createCubieGeometry } from "@/features/cube/helpers/geometry";

export default function Cubie({
  position,
  faceColors,
  setOrbitalControlsEnabled,
  setTurnInput,
}: CubieProps) {
  const [isHovered, setIsHovered] = useState(false);

  const geometry = useMemo(
    () => createCubieGeometry(faceColors, isHovered),
    [faceColors, isHovered]
  );

  return (
    <mesh
      geometry={geometry}
      position={[position.x, position.y, position.z]}
      onPointerDown={(e) => {
        e.stopPropagation();
        setIsHovered(true);

        console.log(
          e.face?.normal
            .toArray()
            .filter((v) => Math.abs(Math.round(v)) === 1)
        );

        setOrbitalControlsEnabled(false);
      }}
      onPointerUp={(e) => {
        e.stopPropagation();
        setIsHovered(false);
        setOrbitalControlsEnabled(true);
      }}
      onPointerEnter={(e) => {
        e.stopPropagation();
        setIsHovered(true);
      }}
      onPointerLeave={(e) => {
        e.stopPropagation();
        setIsHovered(false);
      }}
    >
      <meshStandardMaterial vertexColors />
    </mesh>
  );
}
