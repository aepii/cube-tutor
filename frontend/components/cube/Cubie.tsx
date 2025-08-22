import { useState, useMemo } from "react";
import { CubieProps } from "@/types/cube.types";
import { createCubieGeometry } from "@/utils";

export default function Cubie({
  position,
  faceColors,
  setOrbitalControlsEnabled,
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
