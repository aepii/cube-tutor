import {
  COLORS,
  CubeState,
  applyAlgorithm,
  createSolvedCube,
} from "@/features/cube/engine";
import { parseAlgorithm } from "@/features/cube/helpers/moveParser";
import {
  FACE_SLOT_NORMALS,
  PIECE_POSITIONS,
  faceSlot,
  piecesFromState,
} from "@/features/cube/render/layout";

const scrambled = (): CubeState =>
  applyAlgorithm(createSolvedCube(), parseAlgorithm("R U2 F' L D B2 r M' y"));

describe("face slots", () => {
  it("follow BoxGeometry group order, which matches engine colors R L U D F B", () => {
    expect(FACE_SLOT_NORMALS).toEqual([
      [1, 0, 0],
      [-1, 0, 0],
      [0, 1, 0],
      [0, -1, 0],
      [0, 0, 1],
      [0, 0, -1],
    ]);
    FACE_SLOT_NORMALS.forEach((n, i) => expect(faceSlot(n)).toBe(i));
  });
});

describe("PIECE_POSITIONS", () => {
  it("has all 27 grid positions, including the hidden center", () => {
    expect(PIECE_POSITIONS).toHaveLength(27);
    expect(new Set(PIECE_POSITIONS.map((p) => p.join(","))).size).toBe(27);
  });
});

describe.each([
  ["solved", createSolvedCube],
  ["scrambled", scrambled],
])("piecesFromState (%s)", (_name, makeCube) => {
  const pieces = piecesFromState(makeCube());

  it("colors exactly 54 faces, 9 of each color", () => {
    const colored = pieces.flatMap((p) => p.faces.filter((c) => c !== null));
    expect(colored).toHaveLength(54);
    for (const color of COLORS) {
      expect(colored.filter((c) => c === color)).toHaveLength(9);
    }
  });

  it("gives corners 3 colored faces, edges 2, centers 1, the core 0", () => {
    for (const piece of pieces) {
      const outerAxes = piece.pos.filter((c) => c !== 0).length;
      expect(piece.faces.filter((c) => c !== null)).toHaveLength(outerAxes);
    }
  });

  it("only colors faces that point outward", () => {
    for (const piece of pieces) {
      piece.faces.forEach((color, slot) => {
        if (color === null) return;
        const n = FACE_SLOT_NORMALS[slot];
        const outward = piece.pos[0] * n[0] + piece.pos[1] * n[1] + piece.pos[2] * n[2];
        expect(outward).toBe(1);
      });
    }
  });
});

it("solved cube: each outer face slot shows its own color", () => {
  for (const piece of piecesFromState(createSolvedCube())) {
    piece.faces.forEach((color, slot) => {
      if (color !== null) expect(color).toBe(slot);
    });
  }
});
