import * as THREE from "three";
import type { Coordinates, FaceIndex } from "@/cube/types";
import { useMemo } from "react";
import { faceIndexToFaceColor } from "@/cube/mapping";

export default function Cubie({
  pos,
  faceColors,
}: {
  pos: Coordinates;
  faceColors: Record<FaceIndex, number>;
}) {
  const meshGeometry = useMemo(() => {
    const boxGeometry = new THREE.BoxGeometry(0.95, 0.95, 0.95).toNonIndexed();
    const geometryColors = [];

    const { r: dr, g: dg, b: db } = new THREE.Color(faceIndexToFaceColor(6));

    for (let i = 0; i < 36; i++) {
      geometryColors.push(dr, dg, db);
    }

    for (const faceIndex in faceColors) {
      const colorIndex = faceColors[faceIndex];

      const { r, g, b } = new THREE.Color(faceIndexToFaceColor(colorIndex));

      const vertexStart = faceIndex * 6;

      for (let i = 0; i < 6; i++) {
        const offset = (vertexStart + i) * 3;
        geometryColors[offset] = r;
        geometryColors[offset + 1] = g;
        geometryColors[offset + 2] = b;
      }
    }
    boxGeometry.setAttribute(
      "color",
      new THREE.Float32BufferAttribute(geometryColors, 3)
    );
    return boxGeometry;
  }, [faceColors]);

  return (
    <mesh geometry={meshGeometry} position={[pos.x, pos.y, pos.z]}>
      <meshStandardMaterial vertexColors />
    </mesh>
  );
}
