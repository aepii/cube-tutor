import { Vec3 } from "@/features/cube/engine";
import { parseMove } from "@/features/cube/helpers/moveParser";
import {
  dragAngle,
  literalAngle,
  moveFor,
  resolveTurn,
  snapQuarters,
  turnDurationMs,
} from "@/features/cube/helpers/turnMath";
import { INPUT_CONSTANTS } from "@/features/cube/constants/input.constants";

const Q = Math.PI / 2;
const FRONT: Vec3 = [0, 0, 1];
const RIGHT: Vec3 = [1, 0, 0];
const UP: Vec3 = [0, 1, 0];

// Resolve a drag and snap it to the move it would commit
function dragMove(pos: Vec3, normal: Vec3, drag: Vec3) {
  const turn = resolveTurn(pos, normal, drag);
  if (!turn) return null;
  const quarters = snapQuarters(dragAngle(turn, drag));
  return moveFor(turn.axis, turn.layer, quarters)?.notation ?? null;
}

// One quarter turn's worth of drag along a direction
const quarter = (d: Vec3): Vec3 =>
  d.map((c) => c * INPUT_CONSTANTS.TURN_UNITS_PER_QUARTER) as unknown as Vec3;

describe("resolveTurn + snapping: which move a drag commits", () => {
  it.each<[string, Vec3, Vec3, Vec3, string]>([
    // Front face
    ["front, right column, up", [1, 0, 1], FRONT, [0, 1, 0], "R"],
    ["front, right column, down", [1, -1, 1], FRONT, [0, -1, 0], "R'"],
    ["front, left column, down", [-1, 1, 1], FRONT, [0, -1, 0], "L"],
    ["front, middle column, down", [0, 0, 1], FRONT, [0, -1, 0], "M"],
    ["front, top row, left", [0, 1, 1], FRONT, [-1, 0, 0], "U"],
    ["front, bottom row, right", [1, -1, 1], FRONT, [1, 0, 0], "D"],
    ["front, middle row, right", [-1, 0, 1], FRONT, [1, 0, 0], "E"],
    // Right face
    ["right, front column, up", [1, 0, 1], RIGHT, [0, 1, 0], "F'"],
    ["right, middle column, up", [1, 1, 0], RIGHT, [0, 1, 0], "S'"],
    ["right, back column, up", [1, -1, -1], RIGHT, [0, 1, 0], "B"],
    ["right, top row, toward front", [1, 1, 0], RIGHT, [0, 0, 1], "U"],
    // Up face
    ["up, front row, right", [0, 1, 1], UP, [1, 0, 0], "F"],
    ["up, right column, away", [1, 1, 0], UP, [0, 0, -1], "R"],
  ])("%s → %s", (_name, pos, normal, dir, expected) => {
    expect(dragMove(pos, normal, quarter(dir))).toBe(expected);
  });

  it("ignores drag along the face normal", () => {
    expect(dragMove([1, 0, 1], FRONT, [0, 1.2, 5])).toBe("R");
  });

  it("a short drag snaps back (no move)", () => {
    expect(dragMove([1, 0, 1], FRONT, [0, 0.2, 0])).toBeNull();
  });

  it("a long drag commits a half turn", () => {
    expect(dragMove([1, 0, 1], FRONT, quarter([0, 2, 0]))).toBe("R2");
    expect(dragMove([1, 0, 1], FRONT, quarter([0, -2, 0]))).toBe("R2'");
  });

  it("returns null for no drag", () => {
    expect(resolveTurn([1, 0, 1], FRONT, [0, 0, 0])).toBeNull();
  });
});

describe("literalAngle: moves animate exactly as written", () => {
  it.each([
    ["R", -Q],
    ["R'", Q],
    ["R2", -2 * Q],
    ["R2'", 2 * Q], // counter-clockwise half turn, not normalized
    ["R3", -3 * Q], // 270° clockwise, not R'
    ["L", Q],
    ["M", Q],
    ["U", -Q],
    ["F", -Q],
    ["x", -Q],
  ])("%s", (token, angle) => {
    expect(literalAngle(parseMove(token))).toBeCloseTo(angle);
  });
});

describe("moveFor", () => {
  it("round-trips with literalAngle", () => {
    for (const axis of [0, 1, 2] as const) {
      for (const layer of [-1, 0, 1]) {
        for (const quarters of [-3, -2, -1, 1, 2, 3]) {
          const move = moveFor(axis, layer, quarters)!;
          expect(literalAngle(move)).toBeCloseTo(quarters * Q);
          expect(parseMove(move.notation)).toEqual(move);
        }
      }
    }
  });

  it("returns null for 0 quarters", () => {
    expect(moveFor(0, 1, 0)).toBeNull();
  });
});

describe("snapQuarters / turnDurationMs", () => {
  it("rounds to the nearest quarter turn, never -0", () => {
    expect(snapQuarters(0.7)).toBe(0);
    expect(snapQuarters(0.8)).toBe(1);
    expect(snapQuarters(-2.5)).toBe(-2);
    expect(Object.is(snapQuarters(-0.1), -0)).toBe(false);
  });

  it("is longer for bigger turns, but sub-linear past a quarter", () => {
    const quarterMs = turnDurationMs(Q);
    expect(turnDurationMs(0)).toBe(0);
    expect(turnDurationMs(-Q)).toBe(quarterMs);
    expect(turnDurationMs(2 * Q)).toBeGreaterThan(quarterMs);
    expect(turnDurationMs(2 * Q)).toBeLessThan(2 * quarterMs);
    expect(turnDurationMs(Q, 2)).toBe(quarterMs / 2);
  });
});
