import * as THREE from "three";
import { createSolvedCube } from "@/features/cube/engine";
import { piecesFromState } from "@/features/cube/render/layout";
import {
  PieceUserData,
  dragToLocal,
  pick,
  worldToScreen,
} from "@/features/cube/helpers/screenDrag";
import {
  dragAngle,
  moveFor,
  resolveTurn,
  snapQuarters,
} from "@/features/cube/helpers/turnMath";
import { CAMERA_CONSTANTS } from "@/features/cube/constants/camera.constants";

// A scene like the app's: camera at the default position looking at the
// origin, the cube group (orientation) holding the 27 piece meshes. Plain
// BoxGeometry has the same 6 material groups as the rounded geometry.
const SIZE = { width: 400, height: 400 };

function makeScene(orientation: THREE.Euler) {
  const camera = new THREE.PerspectiveCamera(75, 1, 0.1, 100);
  camera.position.set(...CAMERA_CONSTANTS.DEFAULT_POSITION);
  camera.lookAt(0, 0, 0);
  camera.updateMatrixWorld();

  const cubeGroup = new THREE.Group();
  cubeGroup.quaternion.setFromEuler(orientation);
  const pieces = new THREE.Group();
  cubeGroup.add(pieces);

  const geometry = new THREE.BoxGeometry(0.99, 0.99, 0.99);
  const material = new THREE.MeshBasicMaterial();
  for (const piece of piecesFromState(createSolvedCube())) {
    const mesh = new THREE.Mesh(geometry, Array(6).fill(material));
    mesh.position.set(...piece.pos);
    const data: PieceUserData = {
      pieceKey: piece.key,
      pos: piece.pos,
      colored: piece.faces.map((c) => c !== null),
    };
    mesh.userData = data;
    pieces.add(mesh);
  }
  cubeGroup.updateMatrixWorld(true);
  return { camera, cubeGroup, pieces };
}

// Swipe on screen starting at the center of the front-facing face of the
// piece at world position `worldPos`; returns the committed move.
function swipe(orientation: THREE.Euler, worldPos: [number, number, number], dx: number, dy: number) {
  const { camera, cubeGroup, pieces } = makeScene(orientation);
  const faceCenter = new THREE.Vector3(worldPos[0], worldPos[1], worldPos[2] + 0.495);
  const start = worldToScreen(faceCenter, camera, SIZE);

  const hit = pick(camera, pieces, start, SIZE);
  if (!hit) throw new Error("expected to hit a face");

  const end = { x: start.x + dx, y: start.y + dy };
  const local = dragToLocal(camera, cubeGroup, hit, start, end, SIZE);
  if (!local) throw new Error("drag missed the face plane");

  const turn = resolveTurn(hit.pos, hit.normal, local);
  if (!turn) throw new Error("no turn resolved");
  return { hit, move: moveFor(turn.axis, turn.layer, snapQuarters(dragAngle(turn, local))) };
}

// A swipe a little under one quarter turn's worth on this 400px view: the
// visible height at the front face is ~9.2 cube units (fov 75°, distance 6),
// so ~43px per unit and a quarter turn (1.2 units) is ~52px.
const SWIPE = 45;

describe("pick", () => {
  it("hits the front face of the piece under the point, in cube-local terms", () => {
    const { hit } = swipe(new THREE.Euler(0, 0, 0), [1, 0, 1], 0, -SWIPE);
    expect(hit.pos).toEqual([1, 0, 1]);
    expect(hit.normal).toEqual([0, 0, 1]);
  });

  it("returns null on the background", () => {
    const { camera, pieces } = makeScene(new THREE.Euler(0, 0, 0));
    expect(pick(camera, pieces, { x: 5, y: 5 }, SIZE)).toBeNull();
  });
});

describe("swipes turn the layer you see, however the cube is held", () => {
  it("normal orientation: swipe up on the right column → R", () => {
    expect(swipe(new THREE.Euler(0, 0, 0), [1, 0, 1], 0, -SWIPE).move?.notation).toBe("R");
  });

  it("normal orientation: swipe left on the top row → U", () => {
    expect(swipe(new THREE.Euler(0, 0, 0), [0, 1, 1], -SWIPE, 0).move?.notation).toBe("U");
  });

  it("upside down (z2): swipe up on the visually-right column turns the engine's L layer", () => {
    // z2 swaps left/right and up/down; the visually-right column is L, and
    // moving it visually up is moving it locally down, which is L.
    const { hit, move } = swipe(new THREE.Euler(0, 0, Math.PI), [1, 0, 1], 0, -SWIPE);
    expect(hit.pos).toEqual([-1, 0, 1]);
    expect(move?.notation).toBe("L");
  });

  it("rotated y (green on the right): swipe up on the visually-right column → F", () => {
    // After y, the visible front is the L face and its right column is the F layer
    const { hit, move } = swipe(new THREE.Euler(0, Math.PI / 2, 0), [1, 0, 1], 0, -SWIPE);
    expect(hit.normal).toEqual([-1, 0, 0]);
    expect(move?.notation).toBe("F");
  });
});
