import * as THREE from "three";
import { Vec3 } from "@/features/cube/engine";
import { FACE_SLOT_NORMALS } from "@/features/cube/render/layout";
import { FaceHit, ScreenPoint, ViewSize } from "@/features/cube/types/input.types";

// Screen ↔ 3D helpers for gestures. Pure functions of camera + scene objects
// (no renderer), so they run in unit tests.

const raycaster = new THREE.Raycaster();

// Gesture coordinates (pixels from the view's top-left) → normalized device
// coordinates (-1..1, y up)
export function screenToNdc(p: ScreenPoint, size: ViewSize): THREE.Vector2 {
  return new THREE.Vector2((p.x / size.width) * 2 - 1, -(p.y / size.height) * 2 + 1);
}

// Pixel position of a world point (used by tests)
export function worldToScreen(
  point: THREE.Vector3,
  camera: THREE.Camera,
  size: ViewSize,
): ScreenPoint {
  const ndc = point.clone().project(camera);
  return { x: ((ndc.x + 1) / 2) * size.width, y: ((1 - ndc.y) / 2) * size.height };
}

// Piece meshes carry this in userData (set by CubeModel)
export interface PieceUserData {
  pieceKey: string;
  pos: Vec3;
  // Which face slots are colored (outer); the rest are internal
  colored: boolean[];
}

// The colored face under a screen point, or null (background, or a seam /
// internal face in front). The raycast's materialIndex is the face slot.
export function pick(
  camera: THREE.Camera,
  pieces: THREE.Object3D,
  p: ScreenPoint,
  size: ViewSize,
): FaceHit | null {
  raycaster.setFromCamera(screenToNdc(p, size), camera);
  const hit = raycaster.intersectObjects(pieces.children, true)[0];
  if (!hit) return null;

  const data = hit.object.userData as Partial<PieceUserData>;
  const slot = hit.face?.materialIndex;
  if (!data.pieceKey || !data.pos || !data.colored || slot === undefined) return null;
  if (!data.colored[slot]) return null;

  const normal = FACE_SLOT_NORMALS[slot];
  const worldNormal = new THREE.Vector3(...normal).transformDirection(hit.object.matrixWorld);

  return {
    pieceKey: data.pieceKey,
    pos: data.pos,
    slot,
    normal,
    point: hit.point.clone(),
    worldNormal,
  };
}

// The drag from `start` to `current`, measured on the plane of the touched
// face and expressed in cube-local coordinates (so it works however the cube
// is held). null if a ray misses the plane (face seen edge-on).
export function dragToLocal(
  camera: THREE.Camera,
  cubeGroup: THREE.Object3D,
  hit: FaceHit,
  start: ScreenPoint,
  current: ScreenPoint,
  size: ViewSize,
): Vec3 | null {
  const plane = new THREE.Plane().setFromNormalAndCoplanarPoint(hit.worldNormal, hit.point);

  const project = (p: ScreenPoint) => {
    raycaster.setFromCamera(screenToNdc(p, size), camera);
    return raycaster.ray.intersectPlane(plane, new THREE.Vector3());
  };

  const a = project(start);
  const b = project(current);
  if (!a || !b) return null;

  const toLocal = cubeGroup.getWorldQuaternion(new THREE.Quaternion()).invert();
  const d = b.sub(a).applyQuaternion(toLocal);
  return [d.x, d.y, d.z];
}
