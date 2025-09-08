import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { RotationState } from "@/types";

export function useCubeRotation(rotationState: RotationState) {
  const cubeGroupRef = useRef<THREE.Group>(null);

  useFrame(() => {
    if (!cubeGroupRef.current) return;

    const { x: dx, y: dy, z: dz } = rotationState.value;

    if (dx !== 0) {
      const qx = new THREE.Quaternion().setFromAxisAngle(
        new THREE.Vector3(1, 0, 0),
        dx
      );
      cubeGroupRef.current.quaternion.premultiply(qx);
      rotationState.value = { ...rotationState.value, x: 0 };
    }

    if (dy !== 0) {
      const qy = new THREE.Quaternion().setFromAxisAngle(
        new THREE.Vector3(0, 1, 0),
        dy
      );
      cubeGroupRef.current.quaternion.premultiply(qy);
      rotationState.value = { ...rotationState.value, y: 0 };
    }

    if (dz !== 0) {
      const qz = new THREE.Quaternion().setFromAxisAngle(
        new THREE.Vector3(0, 0, 1),
        dz
      );
      cubeGroupRef.current.quaternion.premultiply(qz);
      rotationState.value = { ...rotationState.value, z: 0 };
    }
  });

  return cubeGroupRef;
}
