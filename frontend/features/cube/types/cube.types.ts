import { RefObject } from "react";
import type * as THREE from "three";

// Cube colors and face conventions live in the engine (engine/types.ts):
// 0..5 = R L U D F B = +X -X +Y -Y +Z -Z, White on Up, Green on Front.

export interface CubeProps {
  // Orientation group (orbiting rotates it)
  cubeGroupRef: RefObject<THREE.Group | null>;
  // Group holding the 27 piece meshes (gestures raycast against it)
  piecesGroupRef: RefObject<THREE.Group | null>;
}
