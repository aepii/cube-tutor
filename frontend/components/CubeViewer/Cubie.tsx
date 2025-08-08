import * as THREE from "three";
import type { Coordinates, FaceIndex } from "@/cube/types";
import { JSX, useMemo } from "react";
import { faceIndexToFaceColor } from "@/cube/mapping";

const FACE_VERTEX_INDICES: Record<FaceIndex, number> = {
  0: 0,
  1: 6,
  2: 12,
  3: 18,
  4: 24,
  5: 30,
  6: -1,
};

export default function Cubie({
  pos,
  faceColors,
}: {
  pos: Coordinates;
  faceColors: Record<FaceIndex, number>;
}) {
  console.log("Creating cubie", pos, faceColors);

  const meshGeometry = useMemo(() => {
    const boxGeometry = new THREE.BoxGeometry().toNonIndexed();
    const geometryColors = new Array(36 * 3).fill(0);

    for (const faceIndex in faceColors) {
      const colorIndex = faceColors[faceIndex];

      const { r, g, b } = new THREE.Color(faceIndexToFaceColor(colorIndex));

      const vertexStart = FACE_VERTEX_INDICES[faceIndex];

      if (vertexStart === -1) throw new Error("Invalid face index");

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
