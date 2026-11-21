import { useLayoutEffect } from "react";
import * as THREE from "three";
import { CubeProps } from "@/features/cube/types/cube.types";
import { CAMERA_CONSTANTS } from "@/features/cube/constants/camera.constants";
import CubeModel from "./CubeModel";

// The outer group holds the cube's orientation (orbiting rotates it); the
// model inside is drawn from engine state.
export default function Cube({ cubeGroupRef, piecesGroupRef }: CubeProps) {
  // Start in a three-quarter view. Set once on mount (not as a prop), so
  // re-renders never reset the orientation the user has dragged to.
  useLayoutEffect(() => {
    const { x, y } = CAMERA_CONSTANTS.INITIAL_TILT;
    cubeGroupRef.current?.quaternion.setFromEuler(new THREE.Euler(x, y, 0, "XYZ"));
  }, [cubeGroupRef]);

  return (
    <group ref={cubeGroupRef}>
      <CubeModel piecesGroupRef={piecesGroupRef} />
    </group>
  );
}
