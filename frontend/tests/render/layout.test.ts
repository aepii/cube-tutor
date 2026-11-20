import { Quaternion, Vector3 } from "three";
import {
  COLORS,
  applyAlgorithm,
  createSolvedCube,
} from "@/features/cube/engine";
import { parseAlgorithm } from "@/features/cube/helpers/moveParser";
import { CORE_HALF } from "@/features/cube/constants/cube.constants";
import { CUBIE_POSITIONS, tilePlacement } from "@/features/cube/render/layout";

const close = (a: number, b: number) => Math.abs(a - b) < 1e-9;

describe("CUBIE_POSITIONS", () => {
  it("has the 26 visible cubies and skips the hidden center", () => {
    expect(CUBIE_POSITIONS).toHaveLength(26);
    expect(CUBIE_POSITIONS.some(([x, y, z]) => x === 0 && y === 0 && z === 0)).toBe(false);
    expect(new Set(CUBIE_POSITIONS.map((p) => p.join(","))).size).toBe(26);
  });
});

describe("tilePlacement", () => {
  const solved = createSolvedCube();

  it("places every tile on the outer surface of its cubie, along its normal", () => {
    for (const sticker of solved) {
      const { position } = tilePlacement(sticker);
      for (let axis = 0; axis < 3; axis++) {
        expect(
          close(position[axis], sticker.pos[axis] + sticker.normal[axis] * CORE_HALF),
        ).toBe(true);
      }
    }
  });

  it("rotates the tile's +Z face to point along the sticker's normal", () => {
    // Includes the -Z face, where the rotation is a 180° turn
    for (const sticker of solved) {
      const [x, y, z, w] = tilePlacement(sticker).quaternion;
      const facing = new Vector3(0, 0, 1).applyQuaternion(new Quaternion(x, y, z, w));
      expect(close(facing.x, sticker.normal[0])).toBe(true);
      expect(close(facing.y, sticker.normal[1])).toBe(true);
      expect(close(facing.z, sticker.normal[2])).toBe(true);
    }
  });

  it("gives 54 distinct tile positions, 9 per face, on a scrambled cube too", () => {
    const scrambled = applyAlgorithm(solved, parseAlgorithm("R U2 F' L D B2 r M' y"));
    const keys = scrambled.map((s) => tilePlacement(s).position.map((n) => n.toFixed(6)).join(","));
    expect(new Set(keys).size).toBe(54);

    for (const color of COLORS) {
      expect(scrambled.filter((s) => s.color === color)).toHaveLength(9);
    }
  });
});
