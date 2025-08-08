import * as THREE from "three";
import type { Coordinates, FaceIndex } from "@/cube/types";
import { useMemo } from "react";
import { faceIndexToFaceColor } from "@/cube/mapping";

// Creates a Cubie component that represents a single cubie of a cube
export default function Cubie({
  pos,
  faceColors,
}: {
  pos: Coordinates;
  faceColors: Map<FaceIndex, FaceIndex>;
}) {
  // Creates a geometry for the cubie with colors based on the face indices
  const meshGeometry = useMemo(() => {
    // Use non-indexed geometry to allow per-face coloring
    const boxGeometry = new THREE.BoxGeometry(0.95, 0.95, 0.95).toNonIndexed();
    // Array to hold colors for each vertex
    const geometryColors = [];

    // Initializes default color for all vertices
    const { r: dr, g: dg, b: db } = new THREE.Color(faceIndexToFaceColor(6));
    for (let i = 0; i < 36; i++) {
      geometryColors.push(dr, dg, db);
    }

    // Assigns colors to vertices based on the face colors
    for (const [faceIndex, colorIndex] of faceColors) {
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
