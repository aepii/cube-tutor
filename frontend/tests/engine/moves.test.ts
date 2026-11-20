import {
  createSolvedCube,
  applyAlgorithm,
  isSolved,
  toFacelets,
} from "@/features/cube/engine";
import { parseAlgorithm } from "@/features/cube/helpers/moveParser";

// Run an algorithm string on a cube (solved by default)
const run = (alg: string, state = createSolvedCube()) =>
  applyAlgorithm(state, parseAlgorithm(alg));

const MOVES = ["R", "L", "U", "D", "F", "B", "M", "E", "S", "x", "y", "z", "r", "l", "u", "d", "f", "b"];

describe("solved state", () => {
  it("a new cube is solved", () => {
    expect(isSolved(createSolvedCube())).toBe(true);
  });

  it("an empty algorithm changes nothing", () => {
    expect(run("")).toEqual(createSolvedCube());
  });
});

describe.each(MOVES)("move %s", (m) => {
  it("changes the state", () => {
    expect(run(m)).not.toEqual(createSolvedCube());
  });

  it("followed by its inverse is the identity", () => {
    expect(run(`${m} ${m}'`)).toEqual(createSolvedCube());
  });

  it("done 4 times is the identity", () => {
    expect(run(`${m} ${m} ${m} ${m}`)).toEqual(createSolvedCube());
  });

  it("2 equals two quarter turns", () => {
    expect(run(`${m}2`)).toEqual(run(`${m} ${m}`));
  });

  it("' equals three quarter turns", () => {
    expect(run(`${m}'`)).toEqual(run(`${m} ${m} ${m}`));
  });
});

describe("move order", () => {
  it("(R U R' U') x6 is the identity, and not before", () => {
    const sexy = "R U R' U' ";
    for (let i = 1; i < 6; i++) {
      expect(isSolved(run(sexy.repeat(i)))).toBe(false);
    }
    expect(isSolved(run(sexy.repeat(6)))).toBe(true);
  });

  it("(R U) has order 105", () => {
    expect(isSolved(run("R U ".repeat(105)))).toBe(true);
    expect(isSolved(run("R U ".repeat(35)))).toBe(false);
  });
});

// These pin the conventions: M follows L, E follows D, S follows F
describe("move relationships", () => {
  it.each([
    ["R L", "L R"], // opposite faces commute
    ["U D", "D U"],
    ["r", "R M'"],
    ["l", "L M"],
    ["u", "U E'"],
    ["d", "D E"],
    ["f", "F S"],
    ["b", "B S'"],
    ["x", "R M' L'"],
    ["y", "U E' D'"],
    ["z", "F S B'"],
  ])("%s equals %s", (a, b) => {
    expect(run(a)).toEqual(run(b));
  });
});

// These pin the turn direction. The identity tests above still pass if every move
// turns the wrong way, so you need at least one concrete state check.
// Facelet string: 54 chars, face order U R F D L B (the format kociemba uses).
describe("direction", () => {
  it("R moves the front's right column up onto U", () => {
    expect(toFacelets(run("R"))).toBe(
      "UUFUUFUUF" + "RRRRRRRRR" + "FFDFFDFFD" + "DDBDDBDDB" + "LLLLLLLLL" + "UBBUBBUBB",
    );
  });

  it("U moves the front's top row to the left face", () => {
    expect(toFacelets(run("U"))).toBe(
      "UUUUUUUUU" + "BBBRRRRRR" + "RRRFFFFFF" + "DDDDDDDDD" + "FFFLLLLLL" + "LLLBBBBBB",
    );
  });
});
