import { Axis, MOVE_TABLE, Vec3 } from "@/features/cube/engine";
import { Move, MoveBase } from "@/features/cube/types/move.types";
import { ResolvedTurn } from "@/features/cube/types/input.types";
import { INPUT_CONSTANTS as I } from "@/features/cube/constants/input.constants";

// Pure math for turning layers by dragging, and for animating moves.
// Angles are radians about the +axis (right-hand rule).

const QUARTER = Math.PI / 2;

const dot = (a: Vec3, b: Vec3) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cross = (a: Vec3, b: Vec3): Vec3 => [
  a[1] * b[2] - a[2] * b[1],
  a[2] * b[0] - a[0] * b[2],
  a[0] * b[1] - a[1] * b[0],
];

// Decides which layer a drag on a face turns.
// - Drop the drag's component along the face normal n.
// - The strongest remaining axis gives the drag direction u.
// - The rotation axis is w = n × u: rotating +90° about w moves the face
//   surface along u (since w × n = u), so the layer follows the finger.
// - The layer is the touched piece's coordinate on that axis.
export function resolveTurn(
  piecePos: Vec3,
  faceNormal: Vec3,
  localDrag: Vec3,
): ResolvedTurn | null {
  const along = dot(localDrag, faceNormal);
  const d: Vec3 = [
    localDrag[0] - faceNormal[0] * along,
    localDrag[1] - faceNormal[1] * along,
    localDrag[2] - faceNormal[2] * along,
  ];

  let best = -1;
  let bestAbs = 0;
  for (let i = 0; i < 3; i++) {
    if (Math.abs(d[i]) > bestAbs) {
      best = i;
      bestAbs = Math.abs(d[i]);
    }
  }
  if (best < 0) return null;

  const s = Math.sign(d[best]);
  const dir: Vec3 = [best === 0 ? s : 0, best === 1 ? s : 0, best === 2 ? s : 0];
  const w = cross(faceNormal, dir);
  const axis = w.findIndex((c) => c !== 0) as Axis;
  if (axis < 0) return null;

  return {
    axis,
    layer: piecePos[axis],
    rotationSign: w[axis] > 0 ? 1 : -1,
    dir,
  };
}

// Live angle of a drag turn: drag distance along the chosen direction,
// one TURN_UNITS_PER_QUARTER = one quarter turn. Dragging back past the
// start turns the other way.
export function dragAngle(turn: ResolvedTurn, localDrag: Vec3): number {
  return (
    turn.rotationSign * (dot(localDrag, turn.dir) / I.TURN_UNITS_PER_QUARTER) * QUARTER
  );
}

// Nearest whole number of quarter turns (never -0)
export function snapQuarters(angle: number): number {
  return Math.round(angle / QUARTER) || 0;
}

const suffix = (turns: number) => {
  const count = Math.abs(turns) === 1 ? "" : String(Math.abs(turns));
  return count + (turns < 0 ? "'" : "");
};

// The single-layer move (R/L/M, U/D/E, F/B/S) that turns `layer` on `axis`
// by `quarters` (signed, about the +axis). null for 0 quarters.
export function moveFor(axis: Axis, layer: number, quarters: number): Move | null {
  if (quarters === 0) return null;
  const base = (Object.keys(MOVE_TABLE) as MoveBase[]).find((b) => {
    const spec = MOVE_TABLE[b];
    return spec.axis === axis && spec.layers.length === 1 && spec.layers[0] === layer;
  });
  if (!base) return null;
  const turns = quarters * MOVE_TABLE[base].sign;
  return { base, turns, notation: base + suffix(turns) };
}

// The angle a move animates through, exactly as written: never reduced, so
// R2' is a counter-clockwise half turn and R3 is 270° clockwise.
export function literalAngle(move: Move): number {
  return move.turns * MOVE_TABLE[move.base].sign * QUARTER;
}

// Animation duration for rotating through `angle` radians.
export function turnDurationMs(angle: number, speed = 1): number {
  const quarters = Math.abs(angle) / QUARTER;
  if (quarters === 0) return 0;
  const scaled = quarters <= 1 ? quarters : 1 + (quarters - 1) * I.EXTRA_QUARTER_FACTOR;
  return (I.QUARTER_TURN_MS * scaled) / speed;
}

export const easeOutCubic = (t: number) => 1 - Math.pow(1 - t, 3);
