import { getCubeCoordinateBounds, getFaceIndices } from "@/cube/helpers";
import { CubeData, FaceIndex } from "@/cube/types";
import { useRef } from "react";
import * as THREE from "three";
import Cubie from "./Cubie";

export default function Cube({ cubeData }: { cubeData: CubeData }) {
  const groupRef = useRef<THREE.Group>(null);

  const size = cubeData[0].length;

  const [minCoord] = getCubeCoordinateBounds(size);

  const cubies = [];

  for (let x = 0; x < size; x++) {
    for (let y = 0; y < size; y++) {
      for (let z = 0; z < size; z++) {
        const cx = minCoord + x;
        const cy = minCoord + y;
        const cz = minCoord + z;

        const faceIndices = getFaceIndices({ x: cx, y: cy, z: cz }, size);
        const faceColors = new Map<FaceIndex, FaceIndex>();
        for (const faceIndex of faceIndices) {
          const color =
            cubeData[faceIndex][
              faceIndex === 2 || faceIndex === 3 ? x : size - 1 - y
            ][faceIndex === 0 || faceIndex === 1 ? size - 1 - z : z];

          faceColors.set(faceIndex, color);
        }

        const key = `${cx},${cy},${cz}`;
        cubies.push({ key, cx, cy, cz, faceColors });
      }
    }
  }

  return (
    <group ref={groupRef}>
      {cubies.map(({ key, cx, cy, cz, faceColors }) => (
        <mesh key={key}>
          <meshBasicMaterial color="black" />
          <Cubie pos={{ x: cx, y: cy, z: cz }} faceColors={faceColors} />
        </mesh>
      ))}
    </group>
  );
}
