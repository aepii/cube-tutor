import { parseAlgorithm, parseMove } from "@/features/cube/helpers/moveParser";
import { applyAlgorithm, createSolvedCube, quarterTurns } from "@/features/cube/engine";

const run = (alg: string) => applyAlgorithm(createSolvedCube(), parseAlgorithm(alg));

describe("parseAlgorithm", () => {
  it("parses basic moves", () => {
    expect(parseAlgorithm("R U R' U'")).toEqual([
      { base: "R", turns: 1, notation: "R" },
      { base: "U", turns: 1, notation: "U" },
      { base: "R", turns: -1, notation: "R'" },
      { base: "U", turns: -1, notation: "U'" },
    ]);
  });

  it("parses lowercase wide moves", () => {
    expect(parseAlgorithm("r' f2")).toEqual([
      { base: "r", turns: -1, notation: "r'" },
      { base: "f", turns: 2, notation: "f2" },
    ]);
  });

  it("treats Rw as r but keeps the notation as written", () => {
    expect(parseAlgorithm("Rw2")).toEqual([
      { base: "r", turns: 2, notation: "Rw2" },
    ]);
  });

  it("ignores parentheses and extra spaces", () => {
    expect(parseAlgorithm(" (R U)  R' ").map((m) => m.notation)).toEqual([
      "R",
      "U",
      "R'",
    ]);
  });

  it("rejects unknown moves", () => {
    expect(() => parseAlgorithm("R Q")).toThrow();
    expect(() => parseMove("R0")).toThrow();
    expect(() => parseMove("R'2")).toThrow();
  });
});

// Playback animates the move as written, so the parser must not normalize.
describe("modifiers are preserved as written", () => {
  it.each([
    ["R", 1],
    ["R'", -1],
    ["R2", 2],
    ["R2'", -2],
    ["R3", 3],
    ["R3'", -3],
  ])("%s has %i signed quarter turns", (token, turns) => {
    expect(parseMove(token).turns).toBe(turns);
  });

  it("R2' stays counter-clockwise (not normalized to R2)", () => {
    expect(parseMove("R2'")).toEqual({ base: "R", turns: -2, notation: "R2'" });
  });

  it("R3 stays a 270° clockwise turn (not normalized to R')", () => {
    expect(parseMove("R3")).toEqual({ base: "R", turns: 3, notation: "R3" });
  });
});

// The cube *state* only depends on the turns modulo 4.
describe("state effect of modifiers", () => {
  it.each([
    ["R2'", "R2"],
    ["R3", "R'"],
    ["R3'", "R"],
    ["U2' F3", "U2 F'"],
  ])("%s leaves the same state as %s", (a, b) => {
    expect(run(a)).toEqual(run(b));
  });

  it("R4 is the identity", () => {
    expect(run("R4")).toEqual(createSolvedCube());
  });

  it("quarterTurns reduces signed turns to 0–3 clockwise", () => {
    expect(["R", "R'", "R2", "R2'", "R3", "R4"].map((t) => quarterTurns(parseMove(t)))).toEqual([
      1, 3, 2, 2, 3, 0,
    ]);
  });
});
