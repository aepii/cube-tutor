import type * as THREE from "three";
import type { Axis, Vec3 } from "@/features/cube/engine";

export interface ScreenPoint {
  x: number;
  y: number;
}

export interface ViewSize {
  width: number;
  height: number;
}

// What gesture callbacks (outside the Canvas) need from the R3F scene
export interface SceneHandles {
  camera: THREE.Camera;
  size: ViewSize;
  invalidate: () => void;
}

// A colored face that a screen point hits
export interface FaceHit {
  pieceKey: string;
  // Piece position and face normal in cube-local (engine) coordinates
  pos: Vec3;
  slot: number;
  normal: Vec3;
  // Hit point and face normal in world space (for projecting drags)
  point: THREE.Vector3;
  worldNormal: THREE.Vector3;
}

// The layer a drag turns, decided once per gesture
export interface ResolvedTurn {
  axis: Axis;
  layer: number;
  // Rotation direction about the +axis that moves the face along `dir`
  rotationSign: 1 | -1;
  // Unit drag direction across the face, cube-local
  dir: Vec3;
}

export interface FaceRef {
  pieceKey: string;
  slot: number;
}
